# fetchers.py - Multi-Agent Fetcher with Axios/httpx and Playwright fallback
import asyncio
import time
from typing import Dict, Optional, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import httpx
import aiohttp
from playwright.async_api import async_playwright, Browser, Page
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from asyncio_throttle import Throttler

logger = structlog.get_logger(__name__)


@dataclass
class FetchResult:
    """Result of a fetch operation"""
    url: str
    success: bool
    content: Optional[str] = None
    status_code: Optional[int] = None
    headers: Optional[Dict[str, str]] = None
    error: Optional[str] = None
    method: str = "unknown"
    fetch_time: float = 0.0
    retry_count: int = 0


class HTTPFetcher:
    """Primary HTTP fetcher using httpx (similar to Axios)"""
    
    def __init__(self, config, compliance_agent):
        self.config = config
        self.compliance_agent = compliance_agent
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(config.HTTP_TIMEOUT),
            headers={"User-Agent": config.USER_AGENT},
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        self.throttler = Throttler(rate_limit=config.MAX_CONCURRENT)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def fetch(self, url: str, retry_count: int = 0) -> FetchResult:
        """Fetch URL with retry logic"""
        start_time = time.time()
        
        try:
            # Check compliance first
            can_scrape, reason = await self.compliance_agent.can_scrape(url)
            if not can_scrape:
                return FetchResult(
                    url=url,
                    success=False,
                    error=f"Compliance check failed: {reason}",
                    method="httpx",
                    fetch_time=time.time() - start_time,
                    retry_count=retry_count
                )
            
            # Throttle requests
            async with self.throttler:
                response = await self.session.get(url)
                response.raise_for_status()
                
                content = response.text
                headers = dict(response.headers)
                
                return FetchResult(
                    url=url,
                    success=True,
                    content=content,
                    status_code=response.status_code,
                    headers=headers,
                    method="httpx",
                    fetch_time=time.time() - start_time,
                    retry_count=retry_count
                )
                
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.reason_phrase}"
            logger.warning(f"HTTP error for {url}: {error_msg}")
            return FetchResult(
                url=url,
                success=False,
                status_code=e.response.status_code,
                error=error_msg,
                method="httpx",
                fetch_time=time.time() - start_time,
                retry_count=retry_count
            )
        except httpx.RequestError as e:
            error_msg = f"Request error: {str(e)}"
            logger.warning(f"Request error for {url}: {error_msg}")
            return FetchResult(
                url=url,
                success=False,
                error=error_msg,
                method="httpx",
                fetch_time=time.time() - start_time,
                retry_count=retry_count
            )
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error for {url}: {error_msg}")
            return FetchResult(
                url=url,
                success=False,
                error=error_msg,
                method="httpx",
                fetch_time=time.time() - start_time,
                retry_count=retry_count
            )


class PlaywrightFetcher:
    """Fallback fetcher using Playwright for dynamic content"""
    
    def __init__(self, config, compliance_agent):
        self.config = config
        self.compliance_agent = compliance_agent
        self.browser: Optional[Browser] = None
        self.context = None
        self.throttler = Throttler(rate_limit=2)  # Lower rate for Playwright
    
    async def __aenter__(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        self.context = await self.browser.new_context(
            user_agent=self.config.USER_AGENT,
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=2, min=4, max=16)
    )
    async def fetch(self, url: str, retry_count: int = 0) -> FetchResult:
        """Fetch URL using Playwright"""
        start_time = time.time()
        
        try:
            # Check compliance first
            can_scrape, reason = await self.compliance_agent.can_scrape(url)
            if not can_scrape:
                return FetchResult(
                    url=url,
                    success=False,
                    error=f"Compliance check failed: {reason}",
                    method="playwright",
                    fetch_time=time.time() - start_time,
                    retry_count=retry_count
                )
            
            # Throttle requests
            async with self.throttler:
                page = await self.context.new_page()
                
                # Set additional headers
                await page.set_extra_http_headers({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                })
                
                # Navigate to page
                response = await page.goto(
                    url, 
                    wait_until='networkidle',
                    timeout=self.config.PLAYWRIGHT_TIMEOUT
                )
                
                if not response:
                    await page.close()
                    return FetchResult(
                        url=url,
                        success=False,
                        error="No response received",
                        method="playwright",
                        fetch_time=time.time() - start_time,
                        retry_count=retry_count
                    )
                
                # Get content
                content = await page.content()
                headers = response.headers
                
                await page.close()
                
                return FetchResult(
                    url=url,
                    success=True,
                    content=content,
                    status_code=response.status,
                    headers=dict(headers),
                    method="playwright",
                    fetch_time=time.time() - start_time,
                    retry_count=retry_count
                )
                
        except Exception as e:
            error_msg = f"Playwright error: {str(e)}"
            logger.warning(f"Playwright error for {url}: {error_msg}")
            return FetchResult(
                url=url,
                success=False,
                error=error_msg,
                method="playwright",
                fetch_time=time.time() - start_time,
                retry_count=retry_count
            )


class MultiAgentFetcher:
    """Orchestrates multiple fetching strategies"""
    
    def __init__(self, config, compliance_agent):
        self.config = config
        self.compliance_agent = compliance_agent
        self.http_fetcher = HTTPFetcher(config, compliance_agent)
        self.playwright_fetcher = PlaywrightFetcher(config, compliance_agent)
        self.stats = {
            "http_success": 0,
            "http_failed": 0,
            "playwright_success": 0,
            "playwright_failed": 0,
            "total_fetches": 0
        }
    
    async def __aenter__(self):
        await self.http_fetcher.__aenter__()
        await self.playwright_fetcher.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_fetcher.__aexit__(exc_type, exc_val, exc_tb)
        await self.playwright_fetcher.__aexit__(exc_type, exc_val, exc_tb)
    
    async def fetch_with_fallback(self, url: str) -> FetchResult:
        """Fetch URL with HTTP first, Playwright as fallback"""
        self.stats["total_fetches"] += 1
        
        # Try HTTP first
        logger.info(f"Fetching {url} with HTTP")
        result = await self.http_fetcher.fetch(url)
        
        if result.success:
            self.stats["http_success"] += 1
            logger.info(f"HTTP fetch successful for {url}")
            return result
        else:
            self.stats["http_failed"] += 1
            logger.warning(f"HTTP fetch failed for {url}: {result.error}")
        
        # Fallback to Playwright
        logger.info(f"Trying Playwright fallback for {url}")
        result = await self.playwright_fetcher.fetch(url)
        
        if result.success:
            self.stats["playwright_success"] += 1
            logger.info(f"Playwright fetch successful for {url}")
        else:
            self.stats["playwright_failed"] += 1
            logger.error(f"Playwright fetch also failed for {url}: {result.error}")
        
        return result
    
    async def fetch_batch(self, urls: List[str]) -> List[FetchResult]:
        """Fetch multiple URLs concurrently"""
        tasks = [self.fetch_with_fallback(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(FetchResult(
                    url=urls[i],
                    success=False,
                    error=f"Task exception: {str(result)}",
                    method="batch"
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get fetching statistics"""
        total_attempts = self.stats["http_success"] + self.stats["http_failed"] + \
                        self.stats["playwright_success"] + self.stats["playwright_failed"]
        
        return {
            **self.stats,
            "http_success_rate": self.stats["http_success"] / max(total_attempts, 1),
            "playwright_success_rate": self.stats["playwright_success"] / max(total_attempts, 1),
            "overall_success_rate": (self.stats["http_success"] + self.stats["playwright_success"]) / max(total_attempts, 1)
        }