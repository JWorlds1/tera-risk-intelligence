# extractors.py - Specialized extractors for each data source
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag
import structlog
from dateutil import parser as date_parser
import tldextract

from schemas import PageRecord, NASARecord, UNPressRecord, WFPRecord, WorldBankRecord, SCHEMA_MAP
from fetchers import FetchResult
# AI-Extraktion wird nur verwendet wenn OpenAI verfügbar ist
try:
    from ai_agents import EnhancedExtractor
    AI_EXTRACTION_AVAILABLE = True
except Exception as e:
    EnhancedExtractor = None
    AI_EXTRACTION_AVAILABLE = False
from config import Config

logger = structlog.get_logger(__name__)


class BaseExtractor:
    """Base class for all extractors"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.schema_class = SCHEMA_MAP.get(self._get_domain(), PageRecord)
    
    def _get_domain(self) -> str:
        """Get domain for this extractor - to be overridden"""
        return ""
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = tldextract.extract(url)
        return f"{parsed.domain}.{parsed.suffix}"
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove special characters that might cause issues
        text = re.sub(r'[^\w\s\-.,!?;:()]', '', text)
        return text
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract and normalize date from text"""
        if not text:
            return None
        
        # Common date patterns
        date_patterns = [
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4}\b'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(1)
                    parsed_date = date_parser.parse(date_str)
                    return parsed_date.strftime('%Y-%m-%d')
                except:
                    continue
        
        return None
    
    def _extract_region(self, text: str) -> Optional[str]:
        """Extract geographical region from text"""
        if not text:
            return None
        
        # Common region patterns (prioritized by specificity)
        regions = [
            'Horn of Africa', 'Sub-Saharan Africa',  # More specific first
            'East Africa', 'West Africa', 'Central Africa', 'Southern Africa',
            'North Africa',
            'Middle East', 'South Asia', 'Southeast Asia', 'East Asia',
            'Central Asia', 'Latin America', 'Caribbean', 'Central America',
            'South America', 'North America', 'Europe', 'Oceania',
            'Pacific Islands', 'Arctic', 'Antarctic'
        ]
        
        text_lower = text.lower()
        
        # Suche nach Regionen (längere zuerst für bessere Treffer)
        for region in sorted(regions, key=len, reverse=True):
            if region.lower() in text_lower:
                return region
        
        # Fallback: Versuche Länder-Namen zu erkennen und zu Regionen zu mappen
        country_to_region = {
            'kenya': 'East Africa', 'ethiopia': 'East Africa', 'somalia': 'Horn of Africa',
            'uganda': 'East Africa', 'tanzania': 'East Africa', 'rwanda': 'East Africa',
            'sudan': 'North Africa', 'south sudan': 'East Africa', 'eritrea': 'Horn of Africa',
            'djibouti': 'Horn of Africa', 'burundi': 'East Africa',
            'yemen': 'Middle East', 'syria': 'Middle East', 'iraq': 'Middle East',
            'afghanistan': 'South Asia', 'pakistan': 'South Asia', 'bangladesh': 'South Asia',
            'india': 'South Asia', 'nepal': 'South Asia', 'myanmar': 'Southeast Asia',
            'philippines': 'Southeast Asia', 'indonesia': 'Southeast Asia',
            'malaysia': 'Southeast Asia', 'thailand': 'Southeast Asia', 'vietnam': 'Southeast Asia',
            'china': 'East Asia', 'japan': 'East Asia', 'south korea': 'East Asia',
            'north korea': 'East Asia', 'mongolia': 'East Asia',
            'brazil': 'South America', 'mexico': 'North America', 'argentina': 'South America',
            'colombia': 'South America', 'venezuela': 'South America', 'chile': 'South America',
            'peru': 'South America', 'ecuador': 'South America', 'bolivia': 'South America',
            'united states': 'North America', 'usa': 'North America', 'canada': 'North America',
            'germany': 'Europe', 'france': 'Europe', 'italy': 'Europe', 'spain': 'Europe',
            'poland': 'Europe', 'united kingdom': 'Europe', 'uk': 'Europe', 'russia': 'Europe',
            'ukraine': 'Europe'
        }
        
        for country, region in country_to_region.items():
            if country in text_lower:
                return region
        
        return None
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from page"""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http'):
                links.append(href)
            elif href.startswith('/'):
                links.append(urljoin(base_url, href))
        return links
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all image URLs from page"""
        images = []
        for img in soup.find_all('img', src=True):
            src = img['src']
            if src.startswith('http'):
                images.append(src)
            elif src.startswith('/'):
                images.append(urljoin(base_url, src))
        return images
    
    def extract(self, fetch_result: FetchResult) -> Optional[PageRecord]:
        """Extract data from fetch result - to be overridden"""
        if not fetch_result.success or not fetch_result.content:
            return None
        
        try:
            soup = BeautifulSoup(fetch_result.content, 'lxml')
            
            # Basic extraction
            record = self.schema_class(
                url=fetch_result.url,
                source_domain=self._extract_domain(fetch_result.url),
                source_name=self.source_name,
                fetched_at=datetime.now(),
                links=self._extract_links(soup, fetch_result.url),
                image_urls=self._extract_images(soup, fetch_result.url)
            )
            
            return record
        except Exception as e:
            logger.error(f"Error extracting from {fetch_result.url}: {e}")
            return None


class NASAExtractor(BaseExtractor):
    """Extractor for NASA Earth Observatory"""
    
    def __init__(self):
        super().__init__("NASA")
    
    def _get_domain(self) -> str:
        return "earthobservatory.nasa.gov"
    
    def extract(self, fetch_result: FetchResult) -> Optional[NASARecord]:
        if not fetch_result.success or not fetch_result.content:
            return None
        
        try:
            soup = BeautifulSoup(fetch_result.content, 'lxml')
            
            # Extract title
            title_elem = soup.find('h1', class_='article-title') or soup.find('h1')
            title = self._clean_text(title_elem.get_text()) if title_elem else None
            
            # Extract summary/description
            summary_elem = soup.find('div', class_='article-summary') or soup.find('meta', {'name': 'description'})
            if summary_elem:
                if summary_elem.name == 'meta':
                    summary = summary_elem.get('content', '')
                else:
                    summary = self._clean_text(summary_elem.get_text())
            else:
                summary = None
            
            # Extract publish date
            date_elem = soup.find('time') or soup.find('span', class_='date')
            publish_date = None
            if date_elem:
                date_text = date_elem.get_text() or date_elem.get('datetime', '')
                publish_date = self._extract_date(date_text)
            
            # Extract region from title or content
            region = self._extract_region(title or '')
            if not region:
                region = self._extract_region(summary or '')
            
            # Extract topics/tags
            topics = []
            tag_elements = soup.find_all('a', class_='tag') or soup.find_all('span', class_='tag')
            for tag in tag_elements:
                topic = self._clean_text(tag.get_text())
                if topic:
                    topics.append(topic)
            
            # Extract environmental indicators
            indicators = []
            content_text = soup.get_text().lower()
            indicator_keywords = ['ndvi', 'temperature', 'precipitation', 'drought', 'flood', 'fire', 'vegetation', 'soil moisture']
            for keyword in indicator_keywords:
                if keyword in content_text:
                    indicators.append(keyword)
            
            # Extract satellite source
            satellite_source = None
            satellite_elem = soup.find(text=re.compile(r'satellite|landsat|modis|sentinel', re.I))
            if satellite_elem:
                satellite_match = re.search(r'(Landsat|MODIS|Sentinel|Terra|Aqua)', satellite_elem, re.I)
                if satellite_match:
                    satellite_source = satellite_match.group(1)
            
            record = NASARecord(
                url=fetch_result.url,
                source_domain=self._extract_domain(fetch_result.url),
                source_name=self.source_name,
                fetched_at=datetime.now(),
                title=title,
                summary=summary,
                publish_date=publish_date,
                region=region,
                topics=topics,
                content_type="article",
                environmental_indicators=indicators,
                satellite_source=satellite_source,
                links=self._extract_links(soup, fetch_result.url),
                image_urls=self._extract_images(soup, fetch_result.url)
            )
            
            return record
        except Exception as e:
            logger.error(f"Error extracting NASA data from {fetch_result.url}: {e}")
            return None


class UNPressExtractor(BaseExtractor):
    """Extractor for UN Press & Meetings"""
    
    def __init__(self):
        super().__init__("UN Press")
    
    def _get_domain(self) -> str:
        return "press.un.org"
    
    def extract(self, fetch_result: FetchResult) -> Optional[UNPressRecord]:
        if not fetch_result.success or not fetch_result.content:
            return None
        
        try:
            soup = BeautifulSoup(fetch_result.content, 'lxml')
            
            # Extract title
            title_elem = soup.find('h1', class_='page-title') or soup.find('h1')
            title = self._clean_text(title_elem.get_text()) if title_elem else None
            
            # Extract summary
            summary_elem = soup.find('div', class_='field-summary') or soup.find('meta', {'name': 'description'})
            if summary_elem:
                if summary_elem.name == 'meta':
                    summary = summary_elem.get('content', '')
                else:
                    summary = self._clean_text(summary_elem.get_text())
            else:
                summary = None
            
            # Extract date
            date_elem = soup.find('time') or soup.find('span', class_='date')
            publish_date = None
            if date_elem:
                date_text = date_elem.get_text() or date_elem.get('datetime', '')
                publish_date = self._extract_date(date_text)
            
            # Extract region
            region = self._extract_region(title or '')
            if not region:
                region = self._extract_region(summary or '')
            
            # Extract topics
            topics = []
            topic_elements = soup.find_all('a', class_='tag') or soup.find_all('span', class_='topic')
            for topic in topic_elements:
                topic_text = self._clean_text(topic.get_text())
                if topic_text:
                    topics.append(topic_text)
            
            # Check if it's meeting coverage
            meeting_coverage = 'meeting' in (title or '').lower() or 'coverage' in (title or '').lower()
            
            # Check if it's Security Council related
            security_council = 'security council' in (title or '').lower() or 'security council' in (summary or '').lower()
            
            # Extract speakers
            speakers = []
            speaker_elements = soup.find_all('span', class_='speaker') or soup.find_all('div', class_='speaker')
            for speaker in speaker_elements:
                speaker_text = self._clean_text(speaker.get_text())
                if speaker_text:
                    speakers.append(speaker_text)
            
            record = UNPressRecord(
                url=fetch_result.url,
                source_domain=self._extract_domain(fetch_result.url),
                source_name=self.source_name,
                fetched_at=datetime.now(),
                title=title,
                summary=summary,
                publish_date=publish_date,
                region=region,
                topics=topics,
                content_type="press-release",
                meeting_coverage=meeting_coverage,
                security_council=security_council,
                speakers=speakers,
                links=self._extract_links(soup, fetch_result.url),
                image_urls=self._extract_images(soup, fetch_result.url)
            )
            
            return record
        except Exception as e:
            logger.error(f"Error extracting UN Press data from {fetch_result.url}: {e}")
            return None


class WFPExtractor(BaseExtractor):
    """Extractor for World Food Programme News"""
    
    def __init__(self):
        super().__init__("WFP")
    
    def _get_domain(self) -> str:
        return "wfp.org"
    
    def extract(self, fetch_result: FetchResult) -> Optional[WFPRecord]:
        if not fetch_result.success or not fetch_result.content:
            return None
        
        try:
            soup = BeautifulSoup(fetch_result.content, 'lxml')
            
            # Extract title
            title_elem = soup.find('h1', class_='article-title') or soup.find('h1')
            title = self._clean_text(title_elem.get_text()) if title_elem else None
            
            # Extract summary
            summary_elem = soup.find('div', class_='article-summary') or soup.find('meta', {'name': 'description'})
            if summary_elem:
                if summary_elem.name == 'meta':
                    summary = summary_elem.get('content', '')
                else:
                    summary = self._clean_text(summary_elem.get_text())
            else:
                summary = None
            
            # Extract date
            date_elem = soup.find('time') or soup.find('span', class_='date')
            publish_date = None
            if date_elem:
                date_text = date_elem.get_text() or date_elem.get('datetime', '')
                publish_date = self._extract_date(date_text)
            
            # Extract region
            region = self._extract_region(title or '')
            if not region:
                region = self._extract_region(summary or '')
            
            # Extract topics
            topics = []
            topic_elements = soup.find_all('a', class_='tag') or soup.find_all('span', class_='category')
            for topic in topic_elements:
                topic_text = self._clean_text(topic.get_text())
                if topic_text:
                    topics.append(topic_text)
            
            # Extract crisis type
            crisis_type = None
            content_text = (title or '') + ' ' + (summary or '')
            crisis_keywords = ['drought', 'flood', 'conflict', 'displacement', 'famine', 'hunger', 'malnutrition']
            for keyword in crisis_keywords:
                if keyword in content_text.lower():
                    crisis_type = keyword
                    break
            
            # Extract affected population
            affected_population = None
            population_match = re.search(r'(\d+(?:,\d+)*)\s*(?:people|individuals|families)', content_text, re.I)
            if population_match:
                affected_population = population_match.group(1)
            
            record = WFPRecord(
                url=fetch_result.url,
                source_domain=self._extract_domain(fetch_result.url),
                source_name=self.source_name,
                fetched_at=datetime.now(),
                title=title,
                summary=summary,
                publish_date=publish_date,
                region=region,
                topics=topics,
                content_type="news",
                crisis_type=crisis_type,
                affected_population=affected_population,
                links=self._extract_links(soup, fetch_result.url),
                image_urls=self._extract_images(soup, fetch_result.url)
            )
            
            return record
        except Exception as e:
            logger.error(f"Error extracting WFP data from {fetch_result.url}: {e}")
            return None


class WorldBankExtractor(BaseExtractor):
    """Extractor for World Bank News"""
    
    def __init__(self):
        super().__init__("World Bank")
    
    def _get_domain(self) -> str:
        return "worldbank.org"
    
    def extract(self, fetch_result: FetchResult) -> Optional[WorldBankRecord]:
        if not fetch_result.success or not fetch_result.content:
            return None
        
        try:
            soup = BeautifulSoup(fetch_result.content, 'lxml')
            
            # Extract title
            title_elem = soup.find('h1', class_='article-title') or soup.find('h1')
            title = self._clean_text(title_elem.get_text()) if title_elem else None
            
            # Extract summary
            summary_elem = soup.find('div', class_='article-summary') or soup.find('meta', {'name': 'description'})
            if summary_elem:
                if summary_elem.name == 'meta':
                    summary = summary_elem.get('content', '')
                else:
                    summary = self._clean_text(summary_elem.get_text())
            else:
                summary = None
            
            # Extract date
            date_elem = soup.find('time') or soup.find('span', class_='date')
            publish_date = None
            if date_elem:
                date_text = date_elem.get_text() or date_elem.get('datetime', '')
                publish_date = self._extract_date(date_text)
            
            # Extract country
            country = None
            country_elem = soup.find('span', class_='country') or soup.find('div', class_='country')
            if country_elem:
                country = self._clean_text(country_elem.get_text())
            else:
                # Try to extract from title or content
                content_text = (title or '') + ' ' + (summary or '')
                country_match = re.search(r'\b(?:in|from|of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', content_text)
                if country_match:
                    country = country_match.group(1)
            
            # Extract sector
            sector = None
            sector_elem = soup.find('span', class_='sector') or soup.find('div', class_='sector')
            if sector_elem:
                sector = self._clean_text(sector_elem.get_text())
            else:
                # Try to extract from content
                content_text = (title or '') + ' ' + (summary or '')
                sector_keywords = ['climate', 'agriculture', 'poverty', 'health', 'education', 'infrastructure', 'energy', 'water']
                for keyword in sector_keywords:
                    if keyword in content_text.lower():
                        sector = keyword
                        break
            
            # Extract project ID
            project_id = None
            project_elem = soup.find('span', class_='project-id') or soup.find('div', class_='project-id')
            if project_elem:
                project_id = self._clean_text(project_elem.get_text())
            
            record = WorldBankRecord(
                url=fetch_result.url,
                source_domain=self._extract_domain(fetch_result.url),
                source_name=self.source_name,
                fetched_at=datetime.now(),
                title=title,
                summary=summary,
                publish_date=publish_date,
                region=country,  # Use country as region for World Bank
                topics=[sector] if sector else [],
                content_type="news",
                country=country,
                sector=sector,
                project_id=project_id,
                links=self._extract_links(soup, fetch_result.url),
                image_urls=self._extract_images(soup, fetch_result.url)
            )
            
            return record
        except Exception as e:
            logger.error(f"Error extracting World Bank data from {fetch_result.url}: {e}")
            return None


class ExtractorFactory:
    """Factory for creating appropriate extractors"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.enhanced_extractor = None
        
        if self.config.ENABLE_AI_EXTRACTION and AI_EXTRACTION_AVAILABLE and EnhancedExtractor:
            try:
                self.enhanced_extractor = EnhancedExtractor(
                    self.config, 
                    self.config.FIRECRAWL_API_KEY
                )
                logger.info("AI-unterstützte Extraktion aktiviert (OpenAI)")
            except Exception as e:
                logger.warning(f"AI-Extraktion nicht verfügbar: {e}")
                self.enhanced_extractor = None
        else:
            self.enhanced_extractor = None
            if self.config.ENABLE_AI_EXTRACTION:
                logger.info("AI-Extraktion deaktiviert (OpenAI nicht konfiguriert)")
    
    def get_extractor(self, url: str) -> BaseExtractor:
        """Get appropriate extractor for URL"""
        domain = tldextract.extract(url).domain + '.' + tldextract.extract(url).suffix
        
        if 'earthobservatory.nasa.gov' in domain:
            return NASAExtractor()
        elif 'press.un.org' in domain:
            return UNPressExtractor()
        elif 'wfp.org' in domain:
            return WFPExtractor()
        elif 'worldbank.org' in domain:
            return WorldBankExtractor()
        else:
            return BaseExtractor("Unknown")
    
    async def extract_with_ai(self, url: str, source_name: str) -> Optional[PageRecord]:
        """Extrahiere mit AI-Unterstützung"""
        if not self.enhanced_extractor:
            return None
        
        try:
            return await self.enhanced_extractor.extract_with_ai_support(url, source_name)
        except Exception as e:
            logger.error(f"AI-Extraktion fehlgeschlagen: {e}")
            return None