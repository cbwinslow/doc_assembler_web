"""Interface for integrating with the document generator package."""
from typing import List, Dict, Any, Protocol
from enum import Enum
from pydantic import BaseModel, Field

class DocumentFormat(str, Enum):
    """Supported document formats."""
    PDF = "pdf"
    MARKDOWN = "markdown"
    HTML = "html"

class DocumentTemplate(BaseModel):
    """Model for document templates."""
    name: str = Field(..., min_length=1)
    format: DocumentFormat
    sections: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "name": "research_report",
                "format": "pdf",
                "sections": ["introduction", "methodology", "findings", "conclusion"],
                "metadata": {
                    "author": "Research Team",
                    "version": "1.0",
                    "created_at": "2024-03-16T10:00:00Z"
                }
            }
        }

class DocumentInterface(Protocol):
    """Protocol for document generation integration."""
    
    async def format_research_results(
        self,
        results: Dict[str, Any],
        template: DocumentTemplate
    ) -> str:
        """
        Format research results using template.

        Args:
            results: Dictionary containing research results
            template: DocumentTemplate instance for formatting

        Returns:
            Formatted content as string
        """
        ...

    async def generate_document(
        self,
        content: str,
        template: DocumentTemplate
    ) -> bytes:
        """
        Generate final document.

        Args:
            content: Formatted content string
            template: DocumentTemplate instance for generation

        Returns:
            Generated document as bytes
        """
        ...

    async def validate_template(self, template: DocumentTemplate) -> bool:
        """
        Validate document template.

        Args:
            template: DocumentTemplate instance to validate

        Returns:
            True if template is valid, False otherwise
        """
        ...

