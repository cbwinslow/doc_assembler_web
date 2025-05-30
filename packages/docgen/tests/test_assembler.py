"""Tests for document assembler functionality."""
import pytest
from typing import Dict, Any
from datetime import datetime

from docgen.core.assembler import DocumentAssembler
from docgen.core.template import TemplateConfig
from airesearch.interfaces.document_interface import (
    DocumentFormat,
    DocumentTemplate
)

@pytest.fixture
def assembler():
    """Create document assembler instance."""
    return DocumentAssembler(TemplateConfig(template_dir="tests/templates"))

@pytest.fixture
def sample_template():
    """Create sample document template."""
    return DocumentTemplate(
        name="test_template",
        format=DocumentFormat.HTML,
        sections=["introduction", "methodology", "results", "conclusion"],
        metadata={
            "author": "Test Author",
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat()
        }
    )

@pytest.fixture
def sample_results():
    """Create sample research results."""
    return {
        "title": "Test Research",
        "description": "Test research description",
        "introduction": "This is the introduction section.",
        "methodology": "This is the methodology section.",
        "results": "These are the research results.",
        "conclusion": "This is the conclusion.",
        "tags": ["test", "research"],
        "custom_field": "custom value"
    }

@pytest.mark.asyncio
async def test_format_research_results(
    assembler: DocumentAssembler,
    sample_template: DocumentTemplate,
    sample_results: Dict[str, Any]
):
    """Test research results formatting."""
    formatted_content = await assembler.format_research_results(
        sample_results,
        sample_template
    )
    
    assert formatted_content
    assert "introduction" in formatted_content.lower()
    assert "methodology" in formatted_content.lower()
    assert "results" in formatted_content.lower()
    assert "conclusion" in formatted_content.lower()

@pytest.mark.asyncio
async def test_generate_document_html(
    assembler: DocumentAssembler,
    sample_template: DocumentTemplate
):
    """Test HTML document generation."""
    content = "<h1>Test Content</h1><p>This is a test.</p>"
    document = await assembler.generate_document(content, sample_template)
    
    assert document
    assert isinstance(document, bytes)
    assert b"<!DOCTYPE html>" in document
    assert b"Test Content" in document

@pytest.mark.asyncio
async def test_generate_document_markdown(
    assembler: DocumentAssembler,
    sample_template: DocumentTemplate
):
    """Test Markdown document generation."""
    sample_template.format = DocumentFormat.MARKDOWN
    content = "# Test Content\n\nThis is a test."
    document = await assembler.generate_document(content, sample_template)
    
    assert document
    assert isinstance(document, bytes)
    assert b"# Test Content" in document

@pytest.mark.asyncio
async def test_generate_document_pdf(
    assembler: DocumentAssembler,
    sample_template: DocumentTemplate
):
    """Test PDF document generation."""
    sample_template.format = DocumentFormat.PDF
    content = "<h1>Test Content</h1><p>This is a test.</p>"
    document = await assembler.generate_document(content, sample_template)
    
    assert document
    assert isinstance(document, bytes)
    assert document.startswith(b'%PDF')

@pytest.mark.asyncio
async def test_validate_template(
    assembler: DocumentAssembler,
    sample_template: DocumentTemplate
):
    """Test template validation."""
    # Valid template
    assert await assembler.validate_template(sample_template)
    
    # Invalid template - no name
    invalid_template = DocumentTemplate(
        name="",
        format=DocumentFormat.HTML,
        sections=["test"],
        metadata={}
    )
    assert not await assembler.validate_template(invalid_template)
    
    # Invalid template - no sections
    invalid_template = DocumentTemplate(
        name="test",
        format=DocumentFormat.HTML,
        sections=[],
        metadata={}
    )
    assert not await assembler.validate_template(invalid_template)

@pytest.mark.asyncio
async def test_error_handling(
    assembler: DocumentAssembler,
    sample_template: DocumentTemplate
):
    """Test error handling."""
    # Invalid results
    with pytest.raises(RuntimeError):
        await assembler.format_research_results(None, sample_template)
    
    # Invalid content
    with pytest.raises(RuntimeError):
        await assembler.generate_document(None, sample_template)
    
    # Invalid format
    sample_template.format = "invalid"
    with pytest.raises(ValueError):
        await assembler.generate_document("test", sample_template)

@pytest.mark.asyncio
async def test_metadata_handling(
    assembler: DocumentAssembler,
    sample_template: DocumentTemplate,
    sample_results: Dict[str, Any]
):
    """Test metadata handling."""
    formatted_content = await assembler.format_research_results(
        sample_results,
        sample_template
    )
    
    assert formatted_content
    assert "Test Author" in formatted_content
    assert "Test Research" in formatted_content
    assert "custom value" in formatted_content

