"""Document structure models for the docgen package."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentType(Enum):
    """Supported document types."""
    
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"


class HeadingLevel(Enum):
    """Document heading levels."""
    
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4
    H5 = 5
    H6 = 6


@dataclass
class TOCEntry:
    """Table of contents entry."""
    
    title: str
    level: HeadingLevel
    anchor: str
    page_number: Optional[int] = None
    children: List['TOCEntry'] = field(default_factory=list)


@dataclass
class Metadata:
    """Document metadata."""
    
    title: str
    description: Optional[str] = None
    author: Optional[str] = None
    created_date: datetime = field(default_factory=datetime.now)
    modified_date: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    source_url: Optional[str] = None
    language: str = "en"
    custom_fields: Dict[str, str] = field(default_factory=dict)


class DocumentSection(BaseModel):
    """Document section model."""
    
    content: str
    heading: Optional[str] = None
    level: Optional[HeadingLevel] = None
    tags: List[str] = Field(default_factory=list)
    anchor: Optional[str] = None
    page_number: Optional[int] = None


class Document(BaseModel):
    """Main document model."""
    
    content: str
    doc_type: DocumentType
    metadata: Metadata
    sections: List[DocumentSection] = Field(default_factory=list)
    table_of_contents: Optional[List[TOCEntry]] = None
    assets: Dict[str, bytes] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


class DocumentTemplate(BaseModel):
    """Document template model."""
    
    name: str
    description: Optional[str] = None
    template_type: DocumentType
    content: str
    style_template: Optional[str] = None
    metadata_template: Dict[str, str] = Field(default_factory=dict)
    required_fields: List[str] = Field(default_factory=list)

