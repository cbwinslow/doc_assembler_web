"""Template management for document generation."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, Template
from pydantic import BaseModel, Field

from ..models.document import Document, DocumentTemplate, Metadata


class TemplateConfig(BaseModel):
    """Configuration for template management."""
    
    template_dir: str = Field("./templates", description="Directory containing templates")
    default_template: str = Field("default", description="Default template name")
    custom_filters: Dict[str, Any] = Field(default_factory=dict, description="Custom template filters")


class TemplateManager:
    """Manages document templates and template-based generation."""
    
    def __init__(self, config: TemplateConfig):
        """Initialize template manager.
        
        Args:
            config: Template configuration
        """
        self.config = config
        self.env = Environment(
            loader=FileSystemLoader(config.template_dir),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters
        for name, func in config.custom_filters.items():
            self.env.filters[name] = func
        
        # Register built-in filters
        self._register_builtin_filters()
    
    def _register_builtin_filters(self):
        """Register built-in template filters."""
        self.env.filters["format_date"] = lambda d: d.strftime("%Y-%m-%d")
        self.env.filters["to_anchor"] = lambda s: s.lower().replace(" ", "-")
    
    def load_template(self, template_name: str) -> DocumentTemplate:
        """Load a document template.
        
        Args:
            template_name: Name of the template to load
            
        Returns:
            Loaded document template
            
        Raises:
            FileNotFoundError: If template doesn't exist
        """
        template_path = Path(self.config.template_dir) / f"{template_name}.json"
        if not template_path.exists():
            raise FileNotFoundError(f"Template {template_name} not found")
        
        # Load template configuration
        template_config = DocumentTemplate.parse_file(template_path)
        
        # Load associated files
        content_path = template_path.with_suffix(".html")  # or .md based on type
        if content_path.exists():
            template_config.content = content_path.read_text()
        
        style_path = template_path.with_suffix(".css")
        if style_path.exists():
            template_config.style_template = style_path.read_text()
        
        return template_config
    
    def save_template(self, template: DocumentTemplate):
        """Save a document template.
        
        Args:
            template: Template to save
        """
        template_dir = Path(self.config.template_dir)
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # Save template configuration
        template_path = template_dir / f"{template.name}.json"
        template_path.write_text(template.json(indent=2))
        
        # Save associated files
        content_path = template_path.with_suffix(".html")  # or .md based on type
        content_path.write_text(template.content)
        
        if template.style_template:
            style_path = template_path.with_suffix(".css")
            style_path.write_text(template.style_template)
    
    def render_document(
        self,
        document: Document,
        template_name: Optional[str] = None
    ) -> str:
        """Render a document using a template.
        
        Args:
            document: Document to render
            template_name: Optional template name (uses default if not specified)
            
        Returns:
            Rendered document content
        """
        template_name = template_name or self.config.default_template
        template = self.load_template(template_name)
        
        # Create template context
        context = {
            "document": document,
            "metadata": document.metadata,
            "toc": document.table_of_contents,
            "sections": document.sections,
        }
        
        # Render content
        template_obj = Template(template.content)
        rendered_content = template_obj.render(**context)
        
        return rendered_content
    
    def create_metadata_template(self, metadata: Metadata) -> Dict[str, str]:
        """Create a template from document metadata.
        
        Args:
            metadata: Document metadata
            
        Returns:
            Template fields based on metadata
        """
        return {
            "title": metadata.title,
            "description": metadata.description or "",
            "author": metadata.author or "",
            "date": metadata.created_date.strftime("%Y-%m-%d"),
            "tags": ", ".join(metadata.tags),
            **metadata.custom_fields
        }

