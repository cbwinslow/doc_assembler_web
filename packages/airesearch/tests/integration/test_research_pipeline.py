"""Integration tests for the complete research pipeline."""
import pytest
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Callable

from airesearch.core.researcher import ResearchEngine
from airesearch.core.pipeline import ResearchPipeline
from airesearch.models.topic import Topic, ResearchResult
from airesearch.interfaces.crawler_interface import CrawledContent
from airesearch.interfaces.document_interface import DocumentTemplate, DocumentFormat

class MockCrawlerImpl:
    """Mock implementation of crawler interface."""
    
    def __init__(self):
        self.processed_content: List[CrawledContent] = []
    
    async def process_crawled_content(self, content: CrawledContent) -> Dict[str, Any]:
        self.processed_content.append(content)
        return {
            "url": content.url,
            "extracted_text": content.content,
            "metadata": {
                **content.metadata,
                "processed_at": datetime.utcnow().isoformat()
            }
        }
    
    async def extract_relevant_content(self, content: CrawledContent) -> str:
        return f"Relevant content from {content.url}: {content.content}"
    
    async def validate_content(self, content: CrawledContent) -> bool:
        return bool(content.content.strip())

class MockDocumentImpl:
    """Mock implementation of document interface."""
    
    def __init__(self):
        self.generated_documents: List[bytes] = []
    
    async def format_research_results(self, results: Dict[str, Any], template: DocumentTemplate) -> str:
        sections = template.sections
        content_parts = []
        
        for section in sections:
            content_parts.append(f"## {section.title()}")
            if section == "introduction":
                content_parts.append("Introduction to the research topic")
            elif section == "findings":
                content_parts.append("Research findings and analysis")
            elif section == "conclusion":
                content_parts.append("Conclusions and recommendations")
        
        return "\n\n".join(content_parts)
    
    async def generate_document(self, content: str, template: DocumentTemplate) -> bytes:
        result = None
        if template.format == DocumentFormat.PDF:
            result = f"PDF Content: {content}".encode()
        elif template.format == DocumentFormat.MARKDOWN:
            result = content.encode()
        elif template.format == DocumentFormat.HTML:
            result = f"<html><body>{content}</body></html>".encode()
        else:
            raise ValueError(f"Unsupported format: {template.format}")
        
        self.generated_documents.append(result)
        return result
    
    async def validate_template(self, template: DocumentTemplate) -> bool:
        return bool(template.sections)

@pytest.fixture
def mock_crawler() -> MockCrawlerImpl:
    """Create a mock crawler implementation."""
    return MockCrawlerImpl()

@pytest.fixture
def mock_document() -> MockDocumentImpl:
    """Create a mock document implementation."""
    return MockDocumentImpl()

@pytest.fixture
def research_pipeline(
    engine_config,
    mock_crawler,
    mock_document
) -> ResearchPipeline:
    """Create a research pipeline for testing."""
    engine = ResearchEngine(engine_config)
    return ResearchPipeline(engine, mock_crawler, mock_document)

@pytest.mark.asyncio
async def test_complete_pipeline_execution(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate
):
    """Test complete pipeline execution."""
    result = await research_pipeline.execute_research(sample_topic, sample_document_template)
    
    assert isinstance(result, bytes)
    assert len(result) > 0
    assert b"PDF Content" in result or b"<html>" in result or b"#" in result

@pytest.mark.asyncio
async def test_pipeline_with_different_formats(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    markdown_template: DocumentTemplate,
    html_template: DocumentTemplate
):
    """Test pipeline with different output formats."""
    # Test markdown output
    markdown_result = await research_pipeline.execute_research(
        sample_topic,
        markdown_template
    )
    assert isinstance(markdown_result, bytes)
    assert markdown_result.decode().startswith("#")
    
    # Test HTML output
    html_result = await research_pipeline.execute_research(
        sample_topic,
        html_template
    )
    assert isinstance(html_result, bytes)
    assert html_result.decode().startswith("<html>")

@pytest.mark.asyncio
async def test_pipeline_content_processing(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_crawled_content: CrawledContent
):
    """Test content processing in the pipeline."""
    # Add content to the pipeline
    await research_pipeline.add_content(sample_crawled_content)
    
    # Execute research
    result = await research_pipeline.execute_research(sample_topic)
    
    assert isinstance(result, bytes)
    assert sample_crawled_content.url in str(result)
    assert len(research_pipeline.crawler.processed_content) > 0

@pytest.mark.asyncio
async def test_pipeline_error_handling(
    research_pipeline: ResearchPipeline,
    invalid_topic: Topic,
    sample_document_template: DocumentTemplate
):
    """Test pipeline error handling."""
    with pytest.raises(ValueError) as exc_info:
        await research_pipeline.execute_research(invalid_topic, sample_document_template)
    assert "invalid" in str(exc_info.value).lower()

@pytest.mark.asyncio
async def test_pipeline_caching(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    tmp_path: Path
):
    """Test pipeline result caching."""
    cache_dir = tmp_path / "pipeline_cache"
    cache_dir.mkdir()
    research_pipeline.set_cache_dir(cache_dir)
    
    # First execution
    result1 = await research_pipeline.execute_research(
        sample_topic,
        sample_document_template
    )
    
    # Second execution should use cache
    result2 = await research_pipeline.execute_research(
        sample_topic,
        sample_document_template
    )
    
    assert result1 == result2
    assert (cache_dir / f"{sample_topic.id}.cache").exists()
    
    # Check cache content
    cache_file = cache_dir / f"{sample_topic.id}.cache"
    assert cache_file.stat().st_size > 0

@pytest.mark.asyncio
async def test_pipeline_progress_tracking(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate
):
    """Test pipeline progress tracking."""
    progress_updates: List[tuple[str, float]] = []
    
    def progress_callback(stage: str, progress: float) -> None:
        progress_updates.append((stage, progress))
    
    await research_pipeline.execute_research(
        sample_topic,
        sample_document_template,
        progress_callback=progress_callback
    )
    
    assert len(progress_updates) > 0
    assert all(0 <= p <= 1 for _, p in progress_updates)
    assert progress_updates[-1][1] == 1.0  # Final progress should be 100%
    
    # Check stage transitions
    stages = [stage for stage, _ in progress_updates]
    assert "crawling" in stages
    assert "analysis" in stages
    assert "generation" in stages

@pytest.mark.asyncio
async def test_pipeline_with_multiple_content_sources(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate
):
    """Test pipeline with multiple content sources."""
    # Add multiple content sources
    sources = [
        CrawledContent(
            url=f"https://example.com/doc{i}",
            content=f"Test content {i}",
            metadata={"source": f"source{i}"},
            crawled_at=datetime.utcnow()
        ) for i in range(3)
    ]
    
    for source in sources:
        await research_pipeline.add_content(source)
    
    result = await research_pipeline.execute_research(
        sample_topic,
        sample_document_template
    )
    
    assert isinstance(result, bytes)
    assert len(research_pipeline.crawler.processed_content) == len(sources)
    for source in sources:
        assert source.url in str(result)

@pytest.mark.asyncio
async def test_pipeline_cancellation(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate
):
    """Test pipeline cancellation handling."""
    import asyncio
    
    # Create a task that will be cancelled
    task = asyncio.create_task(
        research_pipeline.execute_research(sample_topic, sample_document_template)
    )
    
    # Cancel the task immediately
    task.cancel()
    
    with pytest.raises(asyncio.CancelledError):
        await task

