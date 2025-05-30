"""Interface for integrating with the webcrawler package."""
from typing import List, Dict, Any, Protocol
from datetime import datetime
from pydantic import BaseModel

class CrawledContent(BaseModel):
    """Model for crawled content."""
    url: str
    content: str
    metadata: Dict[str, Any]
    crawled_at: datetime

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "url": "https://example.com/article",
                "content": "Article content here...",
                "metadata": {
                    "title": "Example Article",
                    "author": "John Doe",
                    "published_date": "2024-03-15"
                },
                "crawled_at": "2024-03-16T10:00:00Z"
            }
        }

class CrawlerInterface(Protocol):
    """Protocol for crawler integration."""
    
    async def process_crawled_content(self, content: CrawledContent) -> Dict[str, Any]:
        """
        Process crawled content.

        Args:
            content: CrawledContent instance containing the crawled data

        Returns:
            Dictionary containing processed content and metadata
        """
        ...

    async def extract_relevant_content(self, content: CrawledContent) -> str:
        """
        Extract relevant content from crawled data.

        Args:
            content: CrawledContent instance to extract from

        Returns:
            Extracted relevant content as string
        """
        ...

    async def validate_content(self, content: CrawledContent) -> bool:
        """
        Validate crawled content.

        Args:
            content: CrawledContent instance to validate

        Returns:
            True if content is valid, False otherwise
        """
        ...

