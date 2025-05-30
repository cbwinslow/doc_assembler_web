"""Basic tests for crawler configuration."""

import pytest
from webcrawler.core.config import CrawlerConfig


def test_crawler_config_basic():
    """Test basic crawler configuration creation."""
    config = CrawlerConfig(
        start_url="https://example.com",
        max_depth=3,
        max_pages=100
    )
    
    assert config.start_url == "https://example.com"
    assert config.max_depth == 3
    assert config.max_pages == 100
    assert config.respect_robots_txt is True


def test_crawler_config_invalid_url():
    """Test URL validation in crawler configuration."""
    with pytest.raises(ValueError):
        CrawlerConfig(start_url="invalid-url")


def test_crawler_default_allowed_domains():
    """Test default allowed domains from start URL."""
    config = CrawlerConfig(start_url="https://example.com/path")
    
    assert len(config.allowed_domains) == 1
    assert "example.com" in config.allowed_domains

