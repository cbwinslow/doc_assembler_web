"""
Integration tests for the Playwright crawler implementation.
"""

import asyncio
import pytest
from typing import AsyncGenerator
from playwright.async_api import Page, Browser, BrowserContext

from mcp_server.core.crawler import PlaywrightCrawler, CrawlerConfig, ContentExtraction

# Test data
TEST_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <meta name="description" content="Test description">
</head>
<body>
    <article>
        <h1>Test Content</h1>
        <p>This is a test paragraph.</p>
        <a href="https://example.com/page1">Link 1</a>
        <a href="https://example.com/page2">Link 2</a>
    </article>
    <img src="https://example.com/image.jpg" alt="Test Image">
</body>
</html>
"""

@pytest.fixture
async def test_page(page: Page) -> AsyncGenerator[Page, None]:
    """Setup a test page with controlled content."""
    await page.goto("about:blank")
    await page.set_content(TEST_HTML)
    yield page

@pytest.fixture
async def crawler() -> AsyncGenerator[PlaywrightCrawler, None]:
    """Create a test crawler instance."""
    config = CrawlerConfig(
        start_url="about:blank",
        max_depth=2,
        max_pages=10,
        content_types=["documentation"]
    )
    crawler = PlaywrightCrawler(config)
    await crawler.setup()
    yield crawler
    await crawler.cleanup()

async def test_crawler_initialization(crawler: PlaywrightCrawler):
    """Test that the crawler initializes correctly."""
    assert crawler.browser is not None
    assert crawler.context is not None
    assert crawler.page is not None
    assert crawler.config is not None

async def test_content_extraction(crawler: PlaywrightCrawler, test_page: Page):
    """Test that the crawler can extract content correctly."""
    content = await crawler.extract_content(test_page)
    
    assert isinstance(content, ContentExtraction)
    assert "Test Content" in content.content
    assert content.title == "Test Page"
    assert len(content.links) == 2
    assert len(content.assets) == 1
    assert "description" in content.metadata

async def test_rate_limiting(crawler: PlaywrightCrawler):
    """Test that rate limiting works correctly."""
    start_time = asyncio.get_event_loop().time()
    
    # Make multiple requests
    for _ in range(3):
        await crawler.respect_rate_limit()
    
    end_time = asyncio.get_event_loop().time()
    time_taken = end_time - start_time
    
    # With rate limit of 2 requests per second, 3 requests should take at least 1 second
    assert time_taken >= 1.0

async def test_crawl_depth_limit(crawler: PlaywrightCrawler, test_page: Page):
    """Test that the crawler respects depth limits."""
    # Set up a page with links
    test_html = """
    <html>
        <body>
            <a href="https://example.com/depth1">Depth 1</a>
            <a href="https://example.com/depth2">Depth 2</a>
            <a href="https://example.com/depth3">Depth 3</a>
        </body>
    </html>
    """
    await test_page.set_content(test_html)
    
    # Set max depth to 1
    crawler.config.max_depth = 1
    crawler.config.start_url = "https://example.com"
    
    # Mock page navigation
    original_goto = crawler.page.goto
    visited_urls = set()
    
    async def mock_goto(url: str, **kwargs):
        visited_urls.add(url)
        await test_page.set_content(test_html)
        return await original_goto("about:blank")
    
    crawler.page.goto = mock_goto
    
    # Run crawl
    await crawler.crawl()
    
    # Should only visit start URL and depth 1 URLs
    assert len(visited_urls) <= 2

async def test_error_handling(crawler: PlaywrightCrawler, test_page: Page):
    """Test that the crawler handles errors gracefully."""
    # Set up a page that will cause an error
    await test_page.set_content("<html><body>Invalid content")
    
    # Should not raise an exception
    content = await crawler.extract_content(test_page)
    assert content is not None

@pytest.mark.asyncio
async def test_concurrent_crawling(crawler: PlaywrightCrawler):
    """Test that multiple crawl operations can run concurrently."""
    # Create multiple crawl tasks
    tasks = []
    for i in range(3):
        config = CrawlerConfig(
            start_url=f"https://example.com/test{i}",
            max_depth=1,
            max_pages=5
        )
        crawler = PlaywrightCrawler(config)
        await crawler.setup()
        tasks.append(crawler.crawl())
    
    # Run tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check that all tasks completed without raising exceptions
    for result in results:
        assert not isinstance(result, Exception)

@pytest.mark.asyncio
async def test_content_type_filtering(crawler: PlaywrightCrawler, test_page: Page):
    """Test that the crawler correctly filters content by type."""
    # Set up pages with different content types
    doc_html = """
    <html>
        <head>
            <meta name="content-type" content="documentation">
        </head>
        <body>
            <article>Documentation content</article>
        </body>
    </html>
    """
    
    blog_html = """
    <html>
        <head>
            <meta name="content-type" content="blog">
        </head>
        <body>
            <article>Blog content</article>
        </body>
    </html>
    """
    
    # Test documentation content
    await test_page.set_content(doc_html)
    content = await crawler.extract_content(test_page)
    assert "Documentation content" in content.content
    
    # Test non-documentation content
    await test_page.set_content(blog_html)
    content = await crawler.extract_content(test_page)
    assert "Blog content" in content.content

