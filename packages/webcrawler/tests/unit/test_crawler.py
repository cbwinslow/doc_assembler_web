"""Unit tests for the crawler module."""

import asyncio
from typing import AsyncGenerator, List
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
import pytest_asyncio

from webcrawler.core.config import CrawlerConfig, RobotsConfig
from webcrawler.core.crawler import Crawler


# Sample test data
SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <meta name="description" content="Test description">
</head>
<body>
    <h1>Test Page</h1>
    <p>This is a test page.</p>
    <a href="/page1">Link 1</a>
    <a href="/page2">Link 2</a>
    <a href="http://external.com">External Link</a>
</body>
</html>
"""

SAMPLE_ROBOTS_TXT = """
User-agent: *
Disallow: /private/
Allow: /public/
Crawl-delay: 1

User-agent: CloudCurio Crawler
Allow: /
Crawl-delay: 0.5
"""


@pytest.fixture
def crawler_config() -> CrawlerConfig:
    """Create a test crawler configuration."""
    return CrawlerConfig(
        start_url="http://localhost:8080",
        max_depth=2,
        max_pages=10,
        requests_per_second=10.0,
        delay_between_requests=0.1,
        allowed_domains=["localhost"],
        respect_robots_txt=True
    )


async def create_test_app() -> web.Application:
    """Create a test aiohttp application."""
    async def handle_root(request: web.Request) -> web.Response:
        return web.Response(text=SAMPLE_HTML, content_type='text/html')
    
    async def handle_robots(request: web.Request) -> web.Response:
        return web.Response(text=SAMPLE_ROBOTS_TXT, content_type='text/plain')
    
    async def handle_page(request: web.Request) -> web.Response:
        page_num = request.match_info['page']
        return web.Response(
            text=f"<html><body><h1>Page {page_num}</h1></body></html>",
            content_type='text/html'
        )
    
    app = web.Application()
    app.router.add_get('/', handle_root)
    app.router.add_get('/robots.txt', handle_robots)
    app.router.add_get(r'/page{page:\d+}', handle_page)
    return app


@pytest_asyncio.fixture
async def test_server(aiohttp_client) -> TestServer:
    """Create a test server."""
    app = await create_test_app()
    return await aiohttp_client(app)


@pytest.mark.asyncio
async def test_crawler_initialization(crawler_config: CrawlerConfig):
    """Test crawler initialization."""
    crawler = Crawler(crawler_config)
    assert crawler.config == crawler_config
    assert len(crawler.visited_urls) == 0
    assert crawler.session is None


@pytest.mark.asyncio
async def test_fetch_robots_txt(crawler_config: CrawlerConfig, test_server: TestServer):
    """Test fetching and parsing robots.txt."""
    crawler_config.start_url = str(test_server.make_url('/'))
    crawler = Crawler(crawler_config)
    
    async with crawler:
        robots_config = await crawler.fetch_robots_txt('localhost')
        
        assert isinstance(robots_config, RobotsConfig)
        assert len(robots_config.allowed_paths) > 0
        assert len(robots_config.disallowed_paths) > 0
        assert robots_config.crawl_delay == 0.5


@pytest.mark.asyncio
async def test_normalize_url(crawler_config: CrawlerConfig):
    """Test URL normalization."""
    crawler = Crawler(crawler_config)
    base_url = "http://localhost:8080"
    
    # Test relative URL
    assert crawler.normalize_url("/page1", base_url) == "http://localhost:8080/page1"
    
    # Test absolute URL
    assert crawler.normalize_url("http://localhost:8080/page2", base_url) == "http://localhost:8080/page2"
    
    # Test external domain (should return None)
    assert crawler.normalize_url("http://external.com", base_url) is None
    
    # Test invalid URL
    assert crawler.normalize_url("not-a-url", base_url) is None


@pytest.mark.asyncio
async def test_crawl_page(crawler_config: CrawlerConfig, test_server: TestServer):
    """Test crawling a single page."""
    crawler_config.start_url = str(test_server.make_url('/'))
    crawler = Crawler(crawler_config)
    
    async with crawler:
        results = []
        async for url, content, links in crawler.crawl_page(crawler_config.start_url):
            results.append((url, content, links))
        
        assert len(results) > 0
        url, content, links = results[0]
        assert "Test Page" in content
        assert len(links) == 2  # Should only include internal links


@pytest.mark.asyncio
async def test_crawl_with_depth_limit(crawler_config: CrawlerConfig, test_server: TestServer):
    """Test crawling with depth limit."""
    crawler_config.start_url = str(test_server.make_url('/'))
    crawler_config.max_depth = 1
    crawler = Crawler(crawler_config)
    
    async with crawler:
        results = []
        async for result in crawler.crawl():
            results.append(result)
        
        assert len(results) == 1  # Should only crawl the start page


@pytest.mark.asyncio
async def test_rate_limiting(crawler_config: CrawlerConfig, test_server: TestServer):
    """Test crawler rate limiting."""
    crawler_config.start_url = str(test_server.make_url('/'))
    crawler_config.delay_between_requests = 0.5
    crawler = Crawler(crawler_config)
    
    async with crawler:
        start_time = asyncio.get_event_loop().time()
        
        # Make multiple requests
        async for _ in crawler.crawl():
            pass
        
        end_time = asyncio.get_event_loop().time()
        time_diff = end_time - start_time
        
        # Should take at least delay_between_requests * number_of_pages
        assert time_diff >= crawler_config.delay_between_requests


@pytest.mark.asyncio
async def test_error_handling(crawler_config: CrawlerConfig):
    """Test crawler error handling."""
    crawler_config.start_url = "http://non-existent-domain.local"
    crawler = Crawler(crawler_config)
    
    async with crawler:
        results = []
        async for result in crawler.crawl():
            results.append(result)
        
        assert len(results) == 0  # Should handle connection error gracefully

