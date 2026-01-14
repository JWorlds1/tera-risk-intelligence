# compliance.py - Advanced Compliance Agent with robots.txt checking and rate limiting
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Set, Optional, List
from urllib.parse import urljoin, urlparse
import httpx
import tldextract
from dataclasses import dataclass
from collections import defaultdict, deque
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


@dataclass
class RateLimitInfo:
    """Rate limiting information for a domain"""
    requests_per_second: float
    last_request_time: float = 0.0
    request_count: int = 0
    window_start: float = 0.0
    max_requests_per_window: int = 100
    window_duration: float = 60.0  # seconds


@dataclass
class RobotsInfo:
    """Robots.txt information for a domain"""
    can_fetch: bool = True
    crawl_delay: float = 1.0
    disallowed_paths: Set[str] = None
    last_checked: Optional[datetime] = None
    
    def __post_init__(self):
        if self.disallowed_paths is None:
            self.disallowed_paths = set()


class ComplianceAgent:
    """Advanced compliance agent for web scraping with robots.txt checking and rate limiting"""
    
    def __init__(self, config):
        self.config = config
        self.rate_limits: Dict[str, RateLimitInfo] = {}
        self.robots_cache: Dict[str, RobotsInfo] = {}
        self.blocked_domains: Set[str] = set()
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            headers={"User-Agent": config.USER_AGENT}
        )
        
        # Initialize rate limits for allowed domains
        for domain in config.ALLOWED_DOMAINS:
            self.rate_limits[domain] = RateLimitInfo(
                requests_per_second=config.RATE_LIMIT,
                max_requests_per_window=int(config.RATE_LIMIT * 60)
            )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = tldextract.extract(url)
        return f"{parsed.domain}.{parsed.suffix}"
    
    def _extract_full_domain(self, url: str) -> str:
        """Extract full domain including subdomain from URL"""
        parsed = tldextract.extract(url)
        if parsed.subdomain:
            return f"{parsed.subdomain}.{parsed.domain}.{parsed.suffix}"
        return f"{parsed.domain}.{parsed.suffix}"
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _fetch_robots_txt(self, domain: str) -> Optional[str]:
        """Fetch robots.txt for a domain with retry logic"""
        try:
            robots_url = f"https://{domain}/robots.txt"
            response = await self.session.get(robots_url)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.warning(f"Failed to fetch robots.txt for {domain}: {e}")
            return None
    
    def _parse_robots_txt(self, robots_content: str, user_agent: str = "*") -> RobotsInfo:
        """Parse robots.txt content"""
        robots_info = RobotsInfo()
        
        if not robots_content:
            return robots_info
        
        lines = robots_content.lower().split('\n')
        current_user_agent = None
        in_our_section = False
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('user-agent:'):
                current_user_agent = line.split(':', 1)[1].strip()
                in_our_section = (current_user_agent == '*' or 
                                user_agent.lower() in current_user_agent.lower())
            elif in_our_section:
                if line.startswith('disallow:'):
                    path = line.split(':', 1)[1].strip()
                    if path:
                        robots_info.disallowed_paths.add(path)
                elif line.startswith('crawl-delay:'):
                    try:
                        delay = float(line.split(':', 1)[1].strip())
                        robots_info.crawl_delay = max(robots_info.crawl_delay, delay)
                    except ValueError:
                        pass
        
        return robots_info
    
    async def check_robots_compliance(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt"""
        domain = self._extract_domain(url)
        
        # Check if domain is blocked
        if domain in self.blocked_domains:
            return False
        
        # Check cache
        if domain in self.robots_cache:
            robots_info = self.robots_cache[domain]
            # Refresh if older than 24 hours
            if (robots_info.last_checked and 
                datetime.now() - robots_info.last_checked < timedelta(hours=24)):
                return self._is_path_allowed(url, robots_info)
        
        # Fetch robots.txt
        robots_content = await self._fetch_robots_txt(domain)
        robots_info = self._parse_robots_txt(robots_content, self.config.USER_AGENT)
        robots_info.last_checked = datetime.now()
        
        self.robots_cache[domain] = robots_info
        
        return self._is_path_allowed(url, robots_info)
    
    def _is_path_allowed(self, url: str, robots_info: RobotsInfo) -> bool:
        """Check if specific path is allowed"""
        if not robots_info.can_fetch:
            return False
        
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        for disallowed_path in robots_info.disallowed_paths:
            if path.startswith(disallowed_path):
                return False
        
        return True
    
    async def wait_for_rate_limit(self, domain: str) -> float:
        """Wait for rate limit and return actual delay used"""
        if domain not in self.rate_limits:
            return 0.0
        
        rate_info = self.rate_limits[domain]
        current_time = time.time()
        
        # Reset window if needed
        if current_time - rate_info.window_start > rate_info.window_duration:
            rate_info.window_start = current_time
            rate_info.request_count = 0
        
        # Check if we need to wait
        time_since_last = current_time - rate_info.last_request_time
        min_interval = 1.0 / rate_info.requests_per_second
        
        if time_since_last < min_interval:
            delay = min_interval - time_since_last
            await asyncio.sleep(delay)
            current_time = time.time()
        
        # Check window limits
        if rate_info.request_count >= rate_info.max_requests_per_window:
            window_remaining = rate_info.window_duration - (current_time - rate_info.window_start)
            if window_remaining > 0:
                await asyncio.sleep(window_remaining)
                current_time = time.time()
                rate_info.window_start = current_time
                rate_info.request_count = 0
        
        # Update counters
        rate_info.last_request_time = current_time
        rate_info.request_count += 1
        
        return current_time - rate_info.last_request_time
    
    async def can_scrape(self, url: str) -> tuple[bool, str]:
        """Check if URL can be scraped (compliance + rate limiting)"""
        domain = self._extract_domain(url)
        full_domain = self._extract_full_domain(url)
        
        # Check if domain is allowed (check both root domain and full domain)
        if domain not in self.config.ALLOWED_DOMAINS and full_domain not in self.config.ALLOWED_DOMAINS:
            return False, f"Domain {domain} not in allowed list"
        
        # Check robots.txt compliance
        if not await self.check_robots_compliance(url):
            return False, f"URL {url} disallowed by robots.txt"
        
        # Wait for rate limit
        await self.wait_for_rate_limit(domain)
        
        return True, "OK"
    
    def block_domain(self, domain: str, reason: str = "Manual block"):
        """Block a domain from scraping"""
        self.blocked_domains.add(domain)
        logger.warning(f"Blocked domain {domain}: {reason}")
    
    def get_stats(self) -> Dict:
        """Get compliance statistics"""
        return {
            "cached_robots": len(self.robots_cache),
            "blocked_domains": len(self.blocked_domains),
            "rate_limited_domains": len(self.rate_limits),
            "total_requests": sum(rl.request_count for rl in self.rate_limits.values())
        }