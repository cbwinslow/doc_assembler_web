"""Document content processor implementation."""

import re
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup
import markdown
from markdown.extensions import toc, meta

from ..models.document import (
    Document,
    DocumentSection,
    DocumentType,
    HeadingLevel,
    Metadata,
    TOCEntry
)


class DocumentProcessor:
    """Processes and analyzes document content."""
    
    def __init__(self):
        """Initialize document processor."""
        self.markdown = markdown.Markdown(extensions=['meta', 'toc'])
    
    def process_document(
        self,
        content: str,
        doc_type: DocumentType,
        metadata: Optional[Metadata] = None
    ) -> Document:
        """Process document content and create structured document.
        
        Args:
            content: Raw document content
            doc_type: Type of the document
            metadata: Optional document metadata
            
        Returns:
            Processed document
        """
        if doc_type == DocumentType.MARKDOWN:
            return self._process_markdown(content, metadata)
        elif doc_type == DocumentType.HTML:
            return self._process_html(content, metadata)
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")
    
    def _process_markdown(self, content: str, metadata: Optional[Metadata] = None) -> Document:
        """Process Markdown content.
        
        Args:
            content: Raw Markdown content
            metadata: Optional document metadata
            
        Returns:
            Processed document
        """
        # Convert Markdown to HTML
        html_content = self.markdown.convert(content)
        
        # Extract metadata from Markdown if not provided
        if not metadata and self.markdown.Meta:
            metadata = self._create_metadata_from_meta(self.markdown.Meta)
        
        # Create document
        document = Document(
            content=content,
            doc_type=DocumentType.MARKDOWN,
            metadata=metadata or Metadata(title="Untitled Document")
        )
        
        # Process sections and TOC
        document.sections = self._extract_sections(html_content)
        document.table_of_contents = self._generate_toc(document.sections)
        
        return document
    
    def _process_html(self, content: str, metadata: Optional[Metadata] = None) -> Document:
        """Process HTML content.
        
        Args:
            content: Raw HTML content
            metadata: Optional document metadata
            
        Returns:
            Processed document
        """
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract metadata from HTML if not provided
        if not metadata:
            metadata = self._extract_html_metadata(soup)
        
        # Create document
        document = Document(
            content=content,
            doc_type=DocumentType.HTML,
            metadata=metadata or Metadata(title="Untitled Document")
        )
        
        # Process sections and TOC
        document.sections = self._extract_sections(content)
        document.table_of_contents = self._generate_toc(document.sections)
        
        return document
    
    def _extract_sections(self, content: str) -> List[DocumentSection]:
        """Extract sections from document content.
        
        Args:
            content: HTML content
            
        Returns:
            List of document sections
        """
        soup = BeautifulSoup(content, 'html.parser')
        sections: List[DocumentSection] = []
        current_section: Optional[DocumentSection] = None
        
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
            if element.name.startswith('h'):
                # Start new section
                if current_section:
                    sections.append(current_section)
                
                level = HeadingLevel(int(element.name[1]))
                current_section = DocumentSection(
                    content="",
                    heading=element.get_text(),
                    level=level,
                    anchor=self._create_anchor(element.get_text())
                )
            elif current_section:
                # Add content to current section
                current_section.content += str(element)
            else:
                # Content before first heading
                current_section = DocumentSection(content=str(element))
        
        # Add last section
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _generate_toc(self, sections: List[DocumentSection]) -> List[TOCEntry]:
        """Generate table of contents from sections.
        
        Args:
            sections: Document sections
            
        Returns:
            Table of contents entries
        """
        toc: List[TOCEntry] = []
        stack: List[TOCEntry] = []
        
        for section in sections:
            if not section.heading or not section.level:
                continue
            
            entry = TOCEntry(
                title=section.heading,
                level=section.level,
                anchor=section.anchor or self._create_anchor(section.heading)
            )
            
            while stack and stack[-1].level.value >= entry.level.value:
                stack.pop()
            
            if stack:
                stack[-1].children.append(entry)
            else:
                toc.append(entry)
            
            stack.append(entry)
        
        return toc
    
    def _create_anchor(self, text: str) -> str:
        """Create HTML anchor from text.
        
        Args:
            text: Source text
            
        Returns:
            Anchor string
        """
        return re.sub(r'[^\w\s-]', '', text).strip().lower().replace(' ', '-')
    
    def _create_metadata_from_meta(self, meta: dict) -> Metadata:
        """Create metadata from Markdown meta information.
        
        Args:
            meta: Markdown metadata dictionary
            
        Returns:
            Document metadata
        """
        return Metadata(
            title=meta.get('title', ['Untitled Document'])[0],
            description=meta.get('description', [None])[0],
            author=meta.get('author', [None])[0],
            tags=meta.get('tags', [''])[0].split(',') if 'tags' in meta else [],
            custom_fields={
                k: v[0] for k, v in meta.items()
                if k not in {'title', 'description', 'author', 'tags'}
            }
        )
    
    def _extract_html_metadata(self, soup: BeautifulSoup) -> Metadata:
        """Extract metadata from HTML content.
        
        Args:
            soup: BeautifulSoup object of HTML content
            
        Returns:
            Document metadata
        """
        metadata = Metadata(title="Untitled Document")
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata.title = title_tag.string or "Untitled Document"
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            content = meta.get('content', '')
            
            if name == 'description':
                metadata.description = content
            elif name == 'author':
                metadata.author = content
            elif name == 'keywords':
                metadata.tags = [tag.strip() for tag in content.split(',')]
            elif name:
                metadata.custom_fields[name] = content
        
        return metadata

