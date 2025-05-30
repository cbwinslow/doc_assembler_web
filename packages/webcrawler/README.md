# CloudCurio WebCrawler

An intelligent and polite web crawler designed for documentation assembly, featuring async processing, rate limiting, and smart content extraction.

## Key Features

- **Asynchronous Processing**: Fast, non-blocking crawling using Python's asyncio
- **Rate Limiting**: Configurable request rates to avoid overwhelming servers
- **robots.txt Compliance**: Respects website crawling policies
- **Domain Scoping**: Smart domain/subdomain handling
- **Error Recovery**: Automatic retries and error handling
- **Content Extraction**: Intelligent HTML processing and link discovery
- **Session Management**: Efficient connection pooling
- **Type Safety**: Full type hinting support
- **Extensible Design**: Easy to customize and extend

## Installation

```bash
# Using poetry (recommended)
poetry add cloudcurio-webcrawler

# Using pip
pip install cloudcurio-webcrawler

# From source
git clone https://github.com/cloudcurio/doc_assembler_web.git
cd doc_assembler_web/packages/webcrawler
poetry install
```

## Quick Start

```python
import asyncio
from webcrawler.core.config import CrawlerConfig
from webcrawler.core.crawler import Crawler

async def main():
    config = CrawlerConfig(
        start_url="https://example.com",
        max_depth=3,
        max_pages=100
    )
    
    async with Crawler(config) as crawler:
        async for url, content, links in crawler.crawl():
            print(f"Crawled: {url}")
            print(f"Found {len(links)} links")

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration Options

### Basic Configuration

```python
config = CrawlerConfig(
    # Required
    start_url="https://example.com",
    
    # Optional with defaults
    max_depth=3,              # Maximum crawl depth
    max_pages=1000,          # Maximum pages to crawl
    requests_per_second=2.0, # Rate limiting
)
```

### Advanced Configuration

```python
config = CrawlerConfig(
    start_url="https://example.com",
    
    # Rate Limiting
    requests_per_second=2.0,
    delay_between_requests=0.5,
    
    # Domain Control
    allowed_domains=["example.com", "docs.example.com"],
    respect_robots_txt=True,
    
    # Request Settings
    timeout=30.0,
    max_retries=3,
    user_agent="CustomBot (+https://example.com/bot)",
    
    # Storage
    storage_path="./crawled_data"
)
```

## API Reference

### Crawler Class

```python
class Crawler:
    async def crawl(self) -> AsyncGenerator[tuple[str, str, list[str]], None]:
        """Start crawling from the configured start URL.
        
        Yields:
            Tuple of (url, content, links) for each crawled page
        """
        
    async def crawl_page(
        self, 
        url: str, 
        depth: int = 0
    ) -> AsyncGenerator[tuple[str, str, list[str]], None]:
        """Crawl a specific page.
        
        Args:
            url: The URL to crawl
            depth: Current crawl depth
            
        Yields:
            Tuple of (url, content, links) for the crawled page
        """
```

## Rate Limiting

The crawler implements two levels of rate limiting:

1. **Global Rate Limiting**:
   ```python
   config = CrawlerConfig(requests_per_second=2.0)
   ```

2. **Per-Domain Rate Limiting**:
   ```python
   config = CrawlerConfig(delay_between_requests=0.5)
   ```

The crawler also respects `Crawl-delay` directives in robots.txt files when `respect_robots_txt=True`.

## robots.txt Handling

### Automatic Parsing

The crawler automatically fetches and parses robots.txt files:

```python
config = CrawlerConfig(
    start_url="https://example.com",
    respect_robots_txt=True  # Default is True
)
```

### Custom Rules

The crawler handles various robots.txt directives:

```
User-agent: *
Disallow: /private/
Allow: /public/
Crawl-delay: 1

User-agent: CloudCurioBot
Allow: /
Crawl-delay: 0.5
```

## Error Handling

The crawler includes comprehensive error handling:

```python
try:
    async with Crawler(config) as crawler:
        async for url, content, links in crawler.crawl():
            try:
                # Process content
                pass
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
except Exception as e:
    logger.error(f"Critical crawler error: {e}")
```

## Advanced Usage

### Custom Content Processing

```python
async def process_crawled_content(url: str, content: str, links: list[str]):
    async with Crawler(config) as crawler:
        async for url, content, links in crawler.crawl():
            # Extract specific content
            soup = BeautifulSoup(content, 'html.parser')
            title = soup.find('title').text
            headings = [h.text for h in soup.find_all(['h1', 'h2', 'h3'])]
            
            # Store results
            save_to_database(url, title, headings)

asyncio.run(process_crawled_content())
```

### Concurrent Processing

```python
async def crawl_multiple_sites(urls: list[str]):
    tasks = []
    for url in urls:
        config = CrawlerConfig(start_url=url)
        crawler = Crawler(config)
        tasks.append(crawler.crawl())
    
    return await asyncio.gather(*tasks)
```

## Development

### Setup Environment

```bash
# Clone repository
git clone https://github.com/cloudcurio/doc_assembler_web.git
cd doc_assembler_web/packages/webcrawler

# Install dependencies
poetry install

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=webcrawler

# Run specific tests
poetry run pytest tests/unit/test_crawler.py
```

### Code Quality

```bash
# Format code
poetry run black .

# Type checking
poetry run mypy src/webcrawler

# Linting
poetry run pylint src/webcrawler
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

