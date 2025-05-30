"""Basic tests for document processor."""

from docgen.core.processor import DocumentProcessor
from docgen.models.document import Document, DocumentType


def test_processor_creation():
    """Test document processor initialization."""
    processor = DocumentProcessor()
    assert processor is not None


def test_process_simple_markdown():
    """Test processing a simple Markdown document."""
    processor = DocumentProcessor()
    content = """# Test Document
    
## Introduction
This is a test.
"""
    
    doc = processor.process_document(
        content=content,
        doc_type=DocumentType.MARKDOWN
    )
    
    assert isinstance(doc, Document)
    assert doc.doc_type == DocumentType.MARKDOWN
    assert doc.metadata.title == "Test Document"
    assert len(doc.sections) > 0


def test_process_empty_document():
    """Test processing an empty document."""
    processor = DocumentProcessor()
    doc = processor.process_document(
        content="",
        doc_type=DocumentType.MARKDOWN
    )
    
    assert isinstance(doc, Document)
    assert not doc.sections

"""Unit tests for the document processor module."""

from datetime import datetime
import pytest
from bs4 import BeautifulSoup

from docgen.core.processor import DocumentProcessor
from docgen.models.document import (
    Document,
    DocumentSection,
    DocumentType,
    HeadingLevel,
    Metadata,
    TOCEntry
)


# Sample test data
SAMPLE_MARKDOWN = """---
title: Test Document
description: A test document
author: Test Author
tags: test, document
---

# Introduction

This is a test document.

## Section 1

This is section 1.

### Subsection 1.1

This is subsection 1.1.

## Section 2

This is section 2.
"""

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Document</title>
    <meta name="description" content="A test document">
    <meta name="author" content="Test Author">
    <meta name="keywords" content="test, document">
</head>
<body>
    <h1>Introduction</h1>
    <p>This is a test document.</p>
    
    <h2>Section 1</h2>
    <p>This is section 1.</p>
    
    <h3>Subsection 1.1</h3>
    <p>This is subsection 1.1.</p>
    
    <h2>Section 2</h2>
    <p>This is section 2.</p>
</body>
</html>
"""


@pytest.fixture
def processor() -> DocumentProcessor:
    """Create a test document processor."""
    return DocumentProcessor()


@pytest.fixture
def sample_metadata() -> Metadata:
    """Create sample metadata."""
    return Metadata(
        title="Test Document",
        description="A test document",
        author="Test Author",
        created_date=datetime.now(),
        modified_date=datetime.now(),
        tags=["test", "document"],
        language="en"
    )


def test_process_markdown(processor: DocumentProcessor):
    """Test processing Markdown content."""
    document = processor.process_document(SAMPLE_MARKDOWN, DocumentType.MARKDOWN)
    
    assert document.doc_type == DocumentType.MARKDOWN
    assert document.metadata.title == "Test Document"
    assert document.metadata.author == "Test Author"
    assert len(document.sections) > 0
    assert document.table_of_contents is not None


def test_process_html(processor: DocumentProcessor):
    """Test processing HTML content."""
    document = processor.process_document(SAMPLE_HTML, DocumentType.HTML)
    
    assert document.doc_type == DocumentType.HTML
    assert document.metadata.title == "Test Document"
    assert document.metadata.author == "Test Author"
    assert len(document.sections) > 0
    assert document.table_of_contents is not None


def test_extract_sections(processor: DocumentProcessor):
    """Test section extraction."""
    document = processor.process_document(SAMPLE_MARKDOWN, DocumentType.MARKDOWN)
    sections = document.sections
    
    assert len(sections) >= 4  # Introduction + 2 sections + 1 subsection
    
    # Verify section structure
    assert sections[0].heading == "Introduction"
    assert sections[0].level == HeadingLevel.H1
    
    assert sections[1].heading == "Section 1"
    assert sections[1].level == HeadingLevel.H2
    
    assert sections[2].heading == "Subsection 1.1"
    assert sections[2].level == HeadingLevel.H3


def test_generate_toc(processor: DocumentProcessor):
    """Test table of contents generation."""
    document = processor.process_document(SAMPLE_MARKDOWN, DocumentType.MARKDOWN)
    toc = document.table_of_contents
    
    assert toc is not None
    assert len(toc) == 1  # One top-level entry (Introduction)
    
    # Verify TOC structure
    intro = toc[0]
    assert intro.title == "Introduction"
    assert intro.level == HeadingLevel.H1
    assert len(intro.children) == 2  # Section 1 and 2
    
    section1 = intro.children[0]
    assert section1.title == "Section 1"
    assert section1.level == HeadingLevel.H2
    assert len(section1.children) == 1  # Subsection 1.1


def test_create_metadata_from_meta(processor: DocumentProcessor):
    """Test metadata extraction from Markdown meta."""
    document = processor.process_document(SAMPLE_MARKDOWN, DocumentType.MARKDOWN)
    metadata = document.metadata
    
    assert metadata.title == "Test Document"
    assert metadata.description == "A test document"
    assert metadata.author == "Test Author"
    assert len(metadata.tags) == 2
    assert "test" in metadata.tags
    assert "document" in metadata.tags


def test_extract_html_metadata(processor: DocumentProcessor):
    """Test metadata extraction from HTML."""
    document = processor.process_document(SAMPLE_HTML, DocumentType.HTML)
    metadata = document.metadata
    
    assert metadata.title == "Test Document"
    assert metadata.description == "A test document"
    assert metadata.author == "Test Author"
    assert len(metadata.tags) == 2
    assert "test" in metadata.tags
    assert "document" in metadata.tags


def test_create_anchor(processor: DocumentProcessor):
    """Test anchor creation."""
    test_cases = [
        ("Test Heading", "test-heading"),
        ("Section 1.2.3!", "section-123"),
        ("  Spaces  ", "spaces"),
        ("Mixed CASE", "mixed-case")
    ]
    
    for input_text, expected in test_cases:
        assert processor._create_anchor(input_text) == expected


def test_error_handling(processor: DocumentProcessor):
    """Test error handling in document processing."""
    # Test invalid document type
    with pytest.raises(ValueError):
        processor.process_document("test", DocumentType.PDF)
    
    # Test invalid Markdown
    invalid_markdown = "# Title\n```python\nunclosed code block"
    document = processor.process_document(invalid_markdown, DocumentType.MARKDOWN)
    assert document is not None  # Should handle invalid Markdown gracefully
    
    # Test invalid HTML
    invalid_html = "<html><unclosed tag>"
    document = processor.process_document(invalid_html, DocumentType.HTML)
    assert document is not None  # Should handle invalid HTML gracefully

