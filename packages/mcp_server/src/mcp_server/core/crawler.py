"""
Playwright-based web crawler for documentation and content extraction.
"""

import asyncio
import hashlib
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page, Response
from pydantic import BaseModel, Field, HttpUrl

logger = logging.getLogger(__name__)

class CrawlerConfig(BaseModel):
    """Configuration for the PlaywrightCrawler."""
    start_url: HttpUrl
    max_depth: int = Field(default=3, ge=1)
    max_pages: int = Field(default=100, ge=1)
    content_types: List[str] = Field(
        default=["documentation", "api", "wiki", "guide", "manual"]
    )
    user_agent: str = Field(
        default="CloudCurio Bot/1.0 (+https://cloudcurio.cc/bot)"
    )
    respect_robots: bool = Field(default=True)
    rate_limit: float = Field(default=2.0, gt=0.0)  # requests per second
    retry_attempts: int = Field(default=3, ge=1)
    retry_delay: float = Field(default=1.0, gt=0.0)
    timeout: float = Field(default=30.0, gt=0.0)
    download_assets: bool = Field(default=True)
    asset_types: List[str] = Field(
        default=[".pdf", ".png", ".jpg", ".jpeg", ".svg", ".gif"]
    )
    max_asset_size: int = Field(default=10_485_760)  # 10MB

class ContentType(BaseModel):
    """Content type classification with confidence score."""
    type: str
    confidence: float = Field(ge=0.0, le=1.0)
    features: List[str]

class Asset(BaseModel):
    """Asset metadata and storage information."""
    url: HttpUrl
    file_type: str
    content_type: str
    size: int
    local_path: Optional[str] = None
    downloaded: bool = False
    error: Optional[str] = None

class ContentExtraction(BaseModel):
    """Extracted and classified content from a webpage."""
    url: HttpUrl
    title: str
    content: str
    html: Optional[str]
    content_type: ContentType
    metadata: Dict[str, Any]
    links: List[HttpUrl]
    assets: List[Asset]
    crawled_at: datetime = Field(default_factory=datetime.utcnow)

class PlaywrightCrawler:
    """Intelligent web crawler using Playwright."""
    
    def __init__(self, config: CrawlerConfig):
        """Initialize the crawler with configuration."""
        self.config = config
        self.browser: Optional[Browser] = None
        self.context: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # State tracking
        self.visited_urls: Set[str] = set()
        self.rate_limiter = asyncio.Semaphore(1)
        self.last_request_time = 0.0
        self.robots_rules: Dict[str, Set[str]] = {}
        
        # Asset management
        self.asset_dir = Path(os.getenv("DATA_DIR", "data")) / "assets"
        self.asset_dir.mkdir(parents=True, exist_ok=True)
    
    async def setup(self) -> None:
        """Initialize Playwright browser and create a new context."""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch()
            self.context = await self.browser.new_context(
                user_agent=self.config.user_agent
            )
            self.page = await self.context.new_page()
            
            # Set up event handlers
            self.page.on("response", self._handle_response)
            await self._setup_request_handling()
            
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.browser:
            await self.browser.close()
    
    async def crawl(self) -> List[ContentExtraction]:
        """Main crawling method."""
        if not self.page:
            raise RuntimeError("Crawler not properly initialized")
        
        results = []
        queue: List[Tuple[str, int]] = [(str(self.config.start_url), 0)]
        
        while queue and len(self.visited_urls) < self.config.max_pages:
            url, depth = queue.pop(0)
            
            if depth > self.config.max_depth or url in self.visited_urls:
                continue
            
            if not self._is_allowed_by_robots(url):
                logger.info(f"Skipping {url} (robots.txt)")
                continue
            
            try:
                await self._respect_rate_limit()
                content = await self._process_url(url, depth)
                if content:
                    results.append(content)
                    
                    if depth < self.config.max_depth:
                        new_urls = self._filter_urls(content.links)
                        queue.extend((url, depth + 1) for url in new_urls)
                        
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                continue
        
        return results
    
    async def _process_url(self, url: str, depth: int) -> Optional[ContentExtraction]:
        """Process a single URL."""
        for attempt in range(self.config.retry_attempts):
            try:
                await self.page.goto(url, timeout=self.config.timeout * 1000)
                await self.page.wait_for_load_state("networkidle")
                
                # Extract content
                content = await self._extract_content()
                if not content:
                    return None
                
                # Classify content
                content_type = await self._classify_content(content)
                if content_type.type not in self.config.content_types:
                    return None
                
                # Process assets
                assets = await self._process_assets() if self.config.download_assets else []
                
                self.visited_urls.add(url)
                return ContentExtraction(
                    url=url,
                    title=content["title"],
                    content=content["text"],
                    html=content.get("html"),
                    content_type=content_type,
                    metadata=content["metadata"],
                    links=content["links"],
                    assets=assets,
                    crawled_at=datetime.utcnow()
                )
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == self.config.retry_attempts - 1:
                    raise
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
    
    async def _extract_content(self) -> Optional[Dict[str, Any]]:
        """Extract content from the current page."""
        try:
            # Get page content
            title = await self.page.title()
            content = await self.page.evaluate("""() => {
                function extractText(element) {
                    const TEXT_NODES = ['P', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'LI', 'CODE', 'PRE'];
                    if (!element) return '';
                    if (TEXT_NODES.includes(element.tagName)) {
                        return element.innerText + '\\n';
                    }
                    let text = '';
                    for (let child of element.children) {
                        text += extractText(child);
                    }
                    return text;
                }
                
                // Try common documentation containers
                const containers = [
                    document.querySelector('article'),
                    document.querySelector('main'),
                    document.querySelector('.documentation'),
                    document.querySelector('.content'),
                    document.body
                ];
                
                for (let container of containers) {
                    if (container) {
                        return extractText(container);
                    }
                }
                return '';
            }""")
            
            # Extract metadata
            metadata = await self.page.evaluate("""() => {
                const metadata = {};
                document.querySelectorAll('meta').forEach(meta => {
                    const name = meta.getAttribute('name') || meta.getAttribute('property');
                    const content = meta.getAttribute('content');
                    if (name && content) metadata[name] = content;
                });
                return metadata;
            }""")
            
            # Extract links
            links = await self.page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a[href]'))
                    .map(a => a.href)
                    .filter(href => href.startsWith('http'));
            }""")
            
            # Get HTML for potential further processing
            html = await self.page.content()
            
            return {
                "title": title,
                "text": content,
                "html": html,
                "metadata": metadata,
                "links": links
            }
            
        except Exception as e:
            logger.error(f"Content extraction failed: {e}")
            return None
    
    async def _classify_content(self, content: Dict[str, Any]) -> ContentType:
        """Classify the content type of the page."""
        features = []
        
        # Check URL patterns
        url = str(self.page.url)
        if re.search(r'/(docs|documentation|wiki|guide|manual)/', url, re.I):
            features.append("url_pattern")
        
        # Check metadata
        metadata = content["metadata"]
        if any(key for key in metadata if "documentation" in key.lower()):
            features.append("metadata_tag")
        
        # Check content markers
        text = content["text"].lower()
        markers = ["installation", "getting started", "api reference", "usage", "example"]
        if any(marker in text for marker in markers):
            features.append("content_markers")
        
        # Calculate confidence
        confidence = min(len(features) / 3, 1.0)
        
        # Determine type
        if confidence >= 0.7:
            doc_type = "documentation"
        elif confidence >= 0.4:
            doc_type = "guide"
        else:
            doc_type = "unknown"
        
        return ContentType(
            type=doc_type,
            confidence=confidence,
            features=features
        )
    
    async def _process_assets(self) -> List[Asset]:
        """Process and download page assets."""
        assets = []
        try:
            # Find asset URLs
            asset_urls = await self.page.evaluate(f"""() => {{
                const assetTypes = {self.config.asset_types};
                return Array.from(document.querySelectorAll(
                    'img[src], a[href], link[href]'
                )).map(el => el.src || el.href)
                .filter(url => url && url.startsWith('http') &&
                    assetTypes.some(type => url.toLowerCase().endsWith(type)));
            }}""")
            
            # Process each asset
            for url in asset_urls:
                try:
                    asset = await self._download_asset(url)
                    if asset:
                        assets.append(asset)
                except Exception as e:
                    logger.warning(f"Asset download failed for {url}: {e}")
            
            return assets
            
        except Exception as e:
            logger.error(f"Asset processing failed: {e}")
            return []
    
    async def _download_asset(self, url: str) -> Optional[Asset]:
        """Download and store an asset."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url) as response:
                    content_type = response.headers.get("content-type", "")
                    size = int(response.headers.get("content-length", 0))
                    
                    if size > self.config.max_asset_size:
                        return Asset(
                            url=url,
                            file_type=Path(url).suffix,
                            content_type=content_type,
                            size=size,
                            error="File too large"
                        )
                    
                    # Download the asset
                    async with session.get(url) as response:
                        if response.status == 200:
                            file_name = f"{hashlib.sha256(url.encode()).hexdigest()}{Path(url).suffix}"
                            file_path = self.asset_dir / file_name
                            
                            async with aiofiles.open(file_path, 'wb') as f:
                                await f.write(await response.read())
                            
                            return Asset(
                                url=url,
                                file_type=Path(url).suffix,
                                content_type=content_type,
                                size=size,
                                local_path=str(file_path),
                                downloaded=True
                            )
            
        except Exception as e:
            return Asset(
                url=url,
                file_type=Path(url).suffix,
                content_type="unknown",
                size=0,
                error=str(e)
            )
    
    async def _respect_rate_limit(self) -> None:
        """Implement rate limiting."""
        async with self.rate_limiter:
            now = asyncio.get_event_loop().time()
            time_since_last = now - self.last_request_time
            if time_since_last < 1.0 / self.config.rate_limit:
                await asyncio.sleep(1.0 / self.config.rate_limit - time_since_last)
            self.last_request_time = now
    
    async def _setup_request_handling(self) -> None:
        """Set up request interception and handling."""
        await self.page.route("**/*", self._handle_request)
    
    async def _handle_request(self, route) -> None:
        """Handle outgoing requests."""
        if not self._is_allowed_by_robots(route.request.url):
            await route.abort()
        else:
            await route.continue_()
    
    async def _handle_response(self, response: Response) -> None:
        """Handle incoming responses."""
        if response.status == 429:  # Too Many Requests
            logger.warning(f"Rate limit hit for {response.url}")
            await asyncio.sleep(self.config.retry_delay * 2)
    
    def _is_allowed_by_robots(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        if not self.config.respect_robots:
            return True
            
        # Implement robots.txt checking
        return True  # Placeholder
    
    def _filter_urls(self, urls: List[str]) -> List[str]:
        """Filter and normalize URLs."""
        base_domain = urlparse(str(self.config.start_url)).netloc
        filtered = []
        
        for url in urls:
            parsed = urlparse(url)
            # Keep URLs from same domain and not visited
            if (parsed.netloc == base_domain and 
                url not in self.visited_urls and
                url not in filtered):
                filtered.append(url)
        
        return filtered
    
    async def __aenter__(self) -> 'PlaywrightCrawler':
        """Async context manager entry."""
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.cleanup()

