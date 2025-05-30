"""Configuration management for the webcrawler package."""

from dataclasses import dataclass
from typing import Dict, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, validator


class CrawlerConfig(BaseModel):
    """Configuration settings for the web crawler."""
    
    # Base crawling settings
    start_url: str = Field(..., description="Starting URL for the crawler")
    max_depth: int = Field(3, description="Maximum depth to crawl")
    max_pages: int = Field(1000, description="Maximum number of pages to crawl")
    
    # Rate limiting settings
    requests_per_second: float = Field(2.0, description="Maximum requests per second")
    delay_between_requests: float = Field(0.5, description="Delay between requests in seconds")
    
    # Domain settings
    allowed_domains: list[str] = Field(default_factory=list, description="List of allowed domains")
    respect_robots_txt: bool = Field(True, description="Whether to respect robots.txt rules")
    
    # Request settings
    timeout: float = Field(30.0, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum number of retries per request")
    user_agent: str = Field(
        "CloudCurio Crawler (+https://cloudcurio.cc)",
        description="User agent string for requests"
    )
    
    # Storage settings
    storage_path: str = Field("./data", description="Path to store crawled data")
    
    @validator("start_url")
    def validate_start_url(cls, v: str) -> str:
        """Validate the start URL format."""
        parsed = urlparse(v)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValueError("start_url must be a valid absolute URL")
        return v
    
    @validator("allowed_domains", pre=True, always=True)
    def set_default_domain(cls, v: list[str], values: Dict) -> list[str]:
        """Set default allowed domain from start_url if not provided."""
        if not v and "start_url" in values:
            parsed = urlparse(values["start_url"])
            return [parsed.netloc]
        return v
    
    def is_allowed_domain(self, url: str) -> bool:
        """Check if a URL's domain is allowed for crawling."""
        parsed = urlparse(url)
        return any(parsed.netloc.endswith(domain) for domain in self.allowed_domains)


@dataclass
class RobotsConfig:
    """Configuration parsed from robots.txt."""
    
    allowed_paths: list[str]
    disallowed_paths: list[str]
    crawl_delay: Optional[float]
    
    def is_allowed(self, path: str) -> bool:
        """Check if a path is allowed by robots.txt rules."""
        from urllib.parse import urlparse
        
        parsed_path = urlparse(path).path
        
        # Check against disallowed paths first
        for disallowed in self.disallowed_paths:
            if parsed_path.startswith(disallowed):
                return False
        
        # If we have explicit allow rules, check them
        if self.allowed_paths:
            return any(parsed_path.startswith(allowed) for allowed in self.allowed_paths)
        
        # If no explicit allow rules, it's allowed if not disallowed
        return True

"""Configuration management for the webcrawler package."""

from dataclasses import dataclass
from typing import Dict, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, validator


class CrawlerConfig(BaseModel):
    """Configuration settings for the web crawler."""
    
    # Base crawling settings
    start_url: str = Field(..., description="Starting URL for the crawler")
    max_depth: int = Field(3, description="Maximum depth to crawl")
    max_pages: int = Field(1000, description="Maximum number of pages to crawl")
    
    # Rate limiting settings
    requests_per_second: float = Field(2.0, description="Maximum requests per second")
    delay_between_requests: float = Field(0.5, description="Delay between requests in seconds")
    
    # Domain settings
    allowed_domains: list[str] = Field(default_factory=list, description="List of allowed domains")
    respect_robots_txt: bool = Field(True, description="Whether to respect robots.txt rules")
    
    # Request settings
    timeout: float = Field(30.0, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum number of retries per request")
    user_agent: str = Field(
        "CloudCurio Crawler (+https://cloudcurio.cc)",
        description="User agent string for requests"
    )
    
    # Storage settings
    storage_path: str = Field("./data", description="Path to store crawled data")
    
    @validator("start_url")
    def validate_start_url(cls, v: str) -> str:
        """Validate the start URL format."""
        parsed = urlparse(v)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValueError("start_url must be a valid absolute URL")
        return v
    
    @validator("allowed_domains", pre=True, always=True)
    def set_default_domain(cls, v: list[str], values: Dict) -> list[str]:
        """Set default allowed domain from start_url if not provided."""
        if not v and "start_url" in values:
            parsed = urlparse(values["start_url"])
            return [parsed.netloc]
        return v
    
    def is_allowed_domain(self, url: str) -> bool:
        """Check if a URL's domain is allowed for crawling."""
        parsed = urlparse(url)
        return any(parsed.netloc.endswith(domain) for domain in self.allowed_domains)


@dataclass
class RobotsConfig:
    """Configuration parsed from robots.txt."""
    
    allowed_paths: list[str]
    disallowed_paths: list[str]
    crawl_delay: Optional[float]
    
    def is_allowed(self, path: str) -> bool:
        """Check if a path is allowed by robots.txt rules."""
        from urllib.parse import urlparse
        
        parsed_path = urlparse(path).path
        
        # Check against disallowed paths first
        for disallowed in self.disallowed_paths:
            if parsed_path.startswith(disallowed):
                return False
        
        # If we have explicit allow rules, check them
        if self.allowed_paths:
            return any(parsed_path.startswith(allowed) for allowed in self.allowed_paths)
        
        # If no explicit allow rules, it's allowed if not disallowed
        return True

