"""Core crawler implementation for the webcrawler package."""

import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional, Set
from urllib.parse import urljoin, urlparse

import aiohttp
from aiohttp import ClientTimeout
from bs4 import BeautifulSoup
import urllib3

from .config import CrawlerConfig, RobotsConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Crawler:
    """Asynchronous web crawler implementation."""
    
    def __init__(self, config: CrawlerConfig):
        """Initialize the crawler with configuration.
        
        Args:
            config: Configuration settings for the crawler
        """
        self.config = config
        self.visited_urls: Set[str] = set()
        self.rate_limiter = asyncio.Semaphore(1)
        self.last_request_time: float = 0
        self.robots_cache: dict[str, RobotsConfig] = {}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Set up the crawler session."""
        timeout = ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={"User-Agent": self.config.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up the crawler session."""
        if self.session:
            await self.session.close()
    
    async def fetch_robots_txt(self, domain: str) -> RobotsConfig:
        """Fetch and parse robots.txt for a domain.
        
        Args:
            domain: The domain to fetch robots

"""Core crawler implementation for the webcrawler package."""

import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional, Set
from urllib.parse import urljoin, urlparse

import aiohttp
from aiohttp import ClientTimeout
from bs4 import BeautifulSoup
import urllib3

from .config import CrawlerConfig, RobotsConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Crawler:
    """Asynchronous web crawler implementation."""
    
    def __init__(self, config: CrawlerConfig):
        """Initialize the crawler with configuration.
        
        Args:
            config: Configuration settings for the crawler
        """
        self.config = config
        self.visited_urls: Set[str] = set()
        self.rate_limiter = asyncio.Semaphore(1)
        self.last_request_time: float = 0
        self.robots_cache: dict[str, RobotsConfig] = {}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Set up the crawler session."""
        timeout = ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={"User-Agent": self.config.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up the crawler session."""
        if self.session:
            await self.session.close()
    
    async def fetch_robots_txt(self, domain: str) -> RobotsConfig:
        """Fetch and parse robots.txt for a domain.
        
        Args:
            domain: The domain to fetch robots.txt from
            
        Returns:
            Parsed robots.txt configuration
        """
        if domain in self.robots_cache:
            return self.robots_cache[domain]
        
        if not self.session:
            raise RuntimeError("Crawler session not initialized")
        
        robots_url = f"https://{domain}/robots.txt"
        allowed_paths = []
        disallowed_paths = []
        crawl_delay = None
        
        try:
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    text = await response.text()
                    current_agent = None
                    
                    for line in text.split('\n'):
                        line = line.strip().lower()
                        if not line or line.startswith('#'):
                            continue
                            
                        if line.startswith('user-agent:'):
                            current_agent = line.split(':', 1)[1].strip()
                        elif current_agent in ['*', self.config.user_agent]:
                            if line.startswith('allow:'):
                                allowed_paths.append(line.split(':', 1)[1].strip())
                            elif line.startswith('disallow:'):
                                disallowed_paths.append(line.split(':', 1)[1].strip())
                            elif line.startswith('crawl-delay:'):
                                try:
                                    crawl_delay = float(line.split(':', 1)[1].strip())
                                except ValueError:
                                    pass
        
        except Exception as e:
            logger.warning(f"Failed to fetch robots.txt from {domain}: {e}")
        
        config = RobotsConfig(allowed_paths, disallowed_paths, crawl_delay)
        self.robots_cache[domain] = config
        return config
    
    async def _wait_for_rate_limit(self):
        """Implement rate limiting between requests."""
        async with self.rate_limiter:
            now = datetime.now().timestamp()
            time_since_last = now - self.last_request_time
            if time_since_last < self.config.delay_between_requests:
                await asyncio.sleep(self.config.delay_between_requests - time_since_last)
            self.last_request_time = datetime.now().timestamp()
    
    def normalize_url(self, url: str, base_url: str) -> Optional[str]:
        """Normalize and validate a URL.
        
        Args:
            url: The URL to normalize
            base_url: The base URL for resolving relative URLs
            
        Returns:
            Normalized URL or None if invalid
        """
        try:
            # Handle relative URLs
            full_url = urljoin(base_url, url)
            parsed = urlparse(full_url)
            
            # Basic validation
            if not all([parsed.scheme, parsed.netloc]):
                return None
            
            # Ensure allowed domain
            if not self.config.is_allowed_domain(full_url):
                return None
            
            # Normalize to consistent format
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
        except Exception as e:
            logger.debug(f"Failed to normalize URL {url}: {e}")
            return None
    
    async def crawl_page(self, url: str, depth: int = 0) -> AsyncGenerator[tuple[str, str, list[str]], None]:
        """Crawl a single page and extract its content and links.
        
        Args:
            url: The URL to crawl
            depth: Current crawl depth
            
        Yields:
            Tuples of (url, content, links) for each crawled page
        """
        if not self.session:
            raise RuntimeError("Crawler session not initialized")
        
        if depth > self.config.max_depth:
            return
        
        if url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        
        # Check robots.txt
        if self.config.respect_robots_txt:
            domain = urlparse(url).netloc
            robots_config = await self.fetch_robots_txt(domain)
            if not robots_config.is_allowed(url):
                logger.info(f"Skipping {url} - disallowed by robots.txt")
                return
        
        # Implement rate limiting
        await self._wait_for_rate_limit()
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status}")
                    return
                
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract links
                links = []
                for link in soup.find_all('a', href=True):
                    normalized = self.normalize_url(link['href'], url)
                    if normalized:
                        links.append(normalized)
                
                yield url, content, links
                
                # Recursively crawl links
                for link in links:
                    if len(self.visited_urls) >= self.config.max_pages:
                        logger.info("Reached maximum number of pages")
                        return
                    
                    async for result in self.crawl_page(link, depth + 1):
                        yield result
                        
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
    
    async def crawl(self) -> AsyncGenerator[tuple[str, str, list[str]], None]:
        """Start crawling from the configured start URL.
        
        Yields:
            Tuples of (url, content, links) for each crawled page
        """
        async with self:
            async for result in self.crawl_page(self.config.start_url):
                yield result

