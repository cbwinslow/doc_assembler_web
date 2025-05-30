"""Document assembler implementation."""
import io
import logging
from typing import Any, Dict, Optional, List
from pathlib import Path
from datetime import datetime

from weasyprint import HTML
from jinja2 import Template
import markdown
from bs4 import BeautifulSoup

from airesearch.interfaces.document_interface import (
    DocumentInterface,
    DocumentFormat,
    DocumentTemplate as AIDocumentTemplate
)
from ..models.document import (
    Document,
    DocumentType,
    DocumentSection,
    Metadata,
    DocumentTemplate as DocgenTemplate
)
from .processor import DocumentProcessor
from .template import TemplateManager, TemplateConfig

logger = logging.getLogger(__name__)

class DocumentAssembler(DocumentInterface):
    """Implements document assembly and generation functionality."""

    def __init__(self, template_config: Optional[TemplateConfig] = None):
        """Initialize document assembler.
        
        Args:
            template_config: Optional template configuration
        """
        self.processor = DocumentProcessor()
        self.template_manager = TemplateManager(
            template_config or TemplateConfig()
        )
        self.markdown = markdown.Markdown(extensions=['meta', 'toc', 'tables'])

    async def format_research_results(
        self,
        results: Dict[str, Any],
        template: AIDocumentTemplate
    ) -> str:
        """Format research results using template.
        
        Args:
            results: Dictionary containing research results
            template: DocumentTemplate instance for formatting
            
        Returns:
            Formatted content as string
            
        Raises:
            ValueError: If template validation fails
            RuntimeError: If formatting fails
        """
        if not results:
            raise RuntimeError("Research results cannot be None or empty")

        try:
            # Validate template
            if not await self.validate_template(template):
                raise ValueError(f"Invalid template: {template.name}")

            # Create metadata
            metadata = self._create_metadata(results, template)

            # Format content based on template type
            if template.format == DocumentFormat.MARKDOWN:
                formatted_content = self._format_markdown_content(results, template)
            else:  # HTML/PDF use HTML formatting
                formatted_content = self._format_html_content(results, template)

            # Process the content
            doc = self.processor.process_document(
                content=formatted_content,
                doc_type=DocumentType(template.format.value),
                metadata=metadata
            )

            # Add sections if not present
            if not doc.sections:
                doc.sections = self._create_sections(results, template)

            # Generate final content
            return self.template_manager.render_document(doc)

        except Exception as e:
            logger.error(f"Error formatting research results: {e}", exc_info=True)
            raise RuntimeError(f"Failed to format research results: {str(e)}")

    async def generate_document(
        self,
        content: str,
        template: AIDocumentTemplate
    ) -> bytes:
        """Generate final document.
        
        Args:
            content: Formatted content string
            template: DocumentTemplate instance for generation
            
        Returns:
            Generated document as bytes
            
        Raises:
            ValueError: If content or template is invalid
            RuntimeError: If document generation fails
        """
        if not content:
            raise RuntimeError("Document content cannot be None or empty")

        try:
            # Validate template
            if not await self.validate_template(template):
                raise ValueError(f"Invalid template: {template.name}")

            # Generate based on format
            if template.format == DocumentFormat.PDF:
                return await self._generate_pdf(content, template)
            elif template.format == DocumentFormat.MARKDOWN:
                return await self._generate_markdown(content, template)
            elif template.format == DocumentFormat.HTML:
                return await self._generate_html(content, template)
            else:
                raise ValueError(f"Unsupported document format: {template.format}")

        except Exception as e:
            logger.error(f"Error generating document: {e}", exc_info=True)
            raise RuntimeError(f"Failed to generate document: {str(e)}")

    async def validate_template(self, template: AIDocumentTemplate) -> bool:
        """Validate document template.
        
        Args:
            template: DocumentTemplate instance to validate
            
        Returns:
            True if template is valid, False otherwise
        """
        try:
            # Basic validation
            if not template.name or not template.format:
                logger.error("Template missing name or format")
                return False

            # Validate format
            if template.format not in DocumentFormat:
                logger.error(f"Invalid template format: {template.format}")
                return False

            # Validate sections
            if not template.sections:
                logger.error("Template has no sections defined")
                return False

            # Validate section names
            if not all(isinstance(s, str) and s.strip() for s in template.sections):
                logger.error("Invalid section names in template")
                return False

            # Validate metadata
            if not isinstance(template.metadata, dict):
                logger.error("Template metadata must be a dictionary")
                return False

            # Try loading template file
            try:
                docgen_template = self._convert_template(template)
                self.template_manager.load_template(template.name)
            except Exception as e:
                logger.error(f"Failed to load template file: {e}")
                return False

            return True

        except Exception as e:
            logger.error(f"Template validation error: {e}")
            return False

    def _create_metadata(
        self,
        results: Dict[str, Any],
        template: AIDocumentTemplate
    ) -> Metadata:
        """Create metadata from results and template.
        
        Args:
            results: Research results
            template: Document template
            
        Returns:
            Document metadata
        """
        return Metadata(
            title=results.get('title', template.name),
            description=results.get('description', ''),
            author=results.get('author', template.metadata.get('author', '')),
            tags=results.get('tags', []),
            created_date=datetime.now(),
            modified_date=datetime.now(),
            custom_fields={
                **template.metadata,
                **{k: v for k, v in results.items() if k not in 
                   ['title', 'description', 'author', 'tags']}
            }
        )

    def _convert_template(self, template: AIDocumentTemplate) -> DocgenTemplate:
        """Convert AI template to docgen template.
        
        Args:
            template: AI DocumentTemplate instance
            
        Returns:
            Docgen DocumentTemplate instance
        """
        return DocgenTemplate(
            name=template.name,
            description=template.metadata.get('description', ''),
            template_type=DocumentType(template.format.value),
            content="",  # Will be loaded from file
            required_fields=template.sections,
            metadata_template=template.metadata
        )

    def _create_sections(
        self,
        results: Dict[str, Any],
        template: AIDocumentTemplate
    ) -> List[DocumentSection]:
        """Create document sections from results.
        
        Args:
            results: Research results
            template: Document template
            
        Returns:
            List of document sections
        """
        sections = []
        for section_name in template.sections:
            if section_name in results:
                sections.append(DocumentSection(
                    content=str(results[section_name]),
                    heading=section_name.title(),
                    tags=[section_name]
                ))
        return sections

    def _format_markdown_content(
        self,
        results: Dict[str, Any],
        template: AIDocumentTemplate
    ) -> str:
        """Format content as Markdown.
        
        Args:
            results: Research results
            template: Document template
            
        Returns:
            Formatted Markdown content
        """
        sections = []
        
        # Add metadata section
        sections.append(f"# {results.get('title', template.name)}\n")
        if 'description' in results:
            sections.append(f"_{results['description']}_\n")
        
        # Add content sections
        for section_name in template.sections:
            if section_name in results:
                sections.append(f"## {section_name.title()}\n")
                sections.append(f"{results[section_name]}\n")
        
        return "\n".join(sections)

    def _format_html_content(
        self,
        results: Dict[str, Any],
        template: AIDocumentTemplate
    ) -> str:
        """Format content as HTML.
        
        Args:
            results: Research results
            template: Document template
            
        Returns:
            Formatted HTML content
        """
        # Convert any Markdown content to HTML
        sections = []
        
        # Add metadata section
        sections.append(f"<h1>{results.get('title', template.name)}</h1>")
        if 'description' in results:
            sections.append(f"<p class='description'>{results['description']}</p>")
        
        # Add content sections
        for section_name in template.sections:
            if section_name in results:
                section_content = str(results[section_name])
                # Convert Markdown to HTML if content appears to be Markdown
                if '##' in section_content or '*' in section_content:
                    section_content = self.markdown.convert(section_content)
                
                sections.append(f"<h2>{section_name.title()}</h2>")
                sections.append(f"<div class='section {section_name}'>{section_content}</div>")
        
        return "\n".join(sections)

    async def _generate_pdf(
        self,
        content: str,
        template: AIDocumentTemplate
    ) -> bytes:
        """Generate PDF document.
        
        Args:
            content: Formatted content
            template: Document template
            
        Returns:
            PDF document as bytes
        """
        try:
            # Convert content to HTML if it's Markdown
            if template.format == DocumentFormat.MARKDOWN:
                content = self.markdown.convert(content)

            # Add base HTML structure if not present
            if not content.strip().startswith('<!DOCTYPE html>'):
                content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; }}
                        h1 {{ color: #2c3e50; }}
                        h2 {{ color: #34495e; }}
                        .description {{ font-style: italic; }}
                    </style>
                </head>
                <body>
                    {content}
                </body>
                </html>
                """

            # Generate PDF
            html = HTML(string=content)
            pdf_buffer = io.BytesIO()
            html.write_pdf(pdf_buffer)
            return pdf_buffer.getvalue()

        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            raise RuntimeError(f"Failed to generate PDF: {str(e)}")

    async def _generate_markdown(
        self,
        content: str,
        template: AIDocumentTemplate
    ) -> bytes:
        """Generate Markdown document.
        
        Args:
            content: Formatted content
            template: Document template
            
        Returns:
            Markdown document as bytes
        """
        try:
            # Convert HTML to Markdown if needed
            if template.format == DocumentFormat.HTML:
                soup = BeautifulSoup(content, 'html.parser')
                content = self._html_to_markdown(soup)

            return content.encode('utf-8')

        except Exception as e:
            logger.error(f"Markdown generation error: {e}")
            raise RuntimeError(f"Failed to generate Markdown: {str(e)}")

    async def _generate_html(
        self,
        content: str,
        template: AIDocumentTemplate
    ) -> bytes:
        """Generate HTML document.
        
        Args:
            content: Formatted content
            template: Document template
            
        Returns:
            HTML document as bytes
        """
        try:
            # Convert Markdown to HTML if needed
            if template.format == DocumentFormat.MARKDOWN:
                content = self.markdown.convert(content)

            # Add base HTML structure if not present
            if not content.strip().startswith('<!DOCTYPE html>'):
                content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; }}
                        h1 {{ color: #2c3e50; }}
                        h2 {{ color: #34495e; }}
                        .description {{ font-style: italic; }}
                    </style>
                </head>
                <body>
                    {content}
                </body>
                </html>
                """

            return content.encode('utf-8')

        except Exception as e:
            logger.error(f"HTML generation error: {e}")
            raise RuntimeError(f"Failed to generate HTML: {str(e)}")

    def _html_to_markdown(self, soup: BeautifulSoup) -> str:
        """Convert HTML to Markdown format.
        
        Args:
            soup: BeautifulSoup object of HTML content
            
        Returns:
            Markdown formatted string
        """
        result = []
        for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'div']):
            if element.name == 'h1':
                result.append(f"# {element.get_text().strip()}\n")
            elif element.name == 'h2':
                result.append(f"## {element.get_text().strip()}\n")
            elif element.name == 'h3':
                result.append(f"### {element.get_text().strip()}\n")
            elif element.name in ['p', 'div']:
                result.append(f"{element.get_text().strip()}\n")
        
        return "\n".join(result)

