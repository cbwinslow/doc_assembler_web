"""Test fixtures for the airesearch package."""
import pytest
from datetime import datetime
from uuid import UUID
from pathlib import Path
from typing import List

from airesearch.core.researcher import ResearchEngineConfig
from airesearch.models.topic import Topic, AnalysisMetrics, ResearchResult
from airesearch.interfaces.crawler_interface import CrawledContent
from airesearch.interfaces.document_interface import DocumentTemplate, DocumentFormat

@pytest.fixture
def sample_topic() -> Topic:
    """Create a sample topic for testing."""
    return Topic(
        title="Machine Learning in Python",
        description="A comprehensive guide to implementing machine learning algorithms using Python",
        keywords=["python", "machine learning", "algorithms", "data science"],
        scope={
            "time_range": "2020-2025",
            "focus": "technical",
            "level": "intermediate"
        }
    )

@pytest.fixture
def sample_metrics() -> AnalysisMetrics:
    """Create sample analysis metrics for testing."""
    return AnalysisMetrics(
        relevance_score=0.85,
        confidence_score=0.92,
        source_quality=0.88,
        coverage_score=0.78
    )

@pytest.fixture
def sample_research_result(sample_topic: Topic) -> ResearchResult:
    """Create a sample research result for testing."""
    return ResearchResult(
        topic_id=sample_topic.id,
        keywords=["python", "scikit-learn", "tensorflow", "machine learning"],
        analysis={
            "main_findings": ["Finding 1", "Finding 2"],
            "trends": ["Trend 1", "Trend 2"],
            "insights": ["Insight 1", "Insight 2"]
        },
        references=[
            "Reference 1",
            "Reference 2"
        ]
    )

@pytest.fixture
def engine_config() -> ResearchEngineConfig:
    """Create a research engine configuration for testing."""
    return ResearchEngineConfig(
        model_name="test-model",
        max_tokens=500,
        temperature=0.7,
        research_depth=2,
        cache_dir=Path("./test_cache")
    )

@pytest.fixture
def sample_text() -> str:
    """Create a sample text for testing text processing."""
    return """
    Machine Learning (ML) is a subset of artificial intelligence that focuses on 
    developing systems that can learn from and make decisions based on data. 
    Popular ML frameworks include TensorFlow and PyTorch. Visit https://pytorch.org 
    for more information. The latest version was released on 2024-03-15 and includes 
    significant improvements in performance, with 25% faster training times.
    """

@pytest.fixture
def mock_crawler_interface():
    """Create a mock crawler interface for testing."""
    from tests.unit.test_interfaces import MockCrawlerInterface
    return MockCrawlerInterface()

@pytest.fixture
def mock_document_interface():
    """Create a mock document interface for testing."""
    from tests.unit.test_interfaces import MockDocumentInterface
    return MockDocumentInterface()

@pytest.fixture
def sample_crawled_content():
    """Create a sample crawled content for testing."""
    return CrawledContent(
        url="https://example.com/test",
        content="Test content for crawling",
        metadata={
            "title": "Test Page",
            "source": "test",
            "timestamp": datetime.utcnow().isoformat()
        },
        crawled_at=datetime.utcnow()
    )

@pytest.fixture
def sample_document_template():
    """Create a sample document template for testing."""
    return DocumentTemplate(
        name="test_report_template",
        format=DocumentFormat.PDF,
        sections=["introduction", "methodology", "findings", "conclusion"],
        metadata={
            "author": "Test Author",
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat()
        }
    )

@pytest.fixture
def invalid_topic() -> Topic:
    """Create an invalid topic for testing error handling."""
    return Topic(
        title="",  # Invalid empty title
        description="Test description",
        keywords=[]
    )

@pytest.fixture
def large_research_result(sample_topic: Topic) -> ResearchResult:
    """Create a large research result for testing pagination and chunking."""
    return ResearchResult(
        topic_id=sample_topic.id,
        keywords=["test"] * 100,  # Large number of keywords
        analysis={
            "main_findings": [f"Finding {i}" for i in range(50)],
            "trends": [f"Trend {i}" for i in range(50)],
            "insights": [f"Insight {i}" for i in range(50)]
        },
        references=[f"Reference {i}" for i in range(100)]
    )

@pytest.fixture
def mock_failed_crawler_interface():
    """Create a mock crawler interface that simulates failures."""
    class FailedMockCrawler:
        async def process_crawled_content(self, content: CrawledContent) -> Dict[str, Any]:
            raise Exception("Simulated crawler failure")
        
        async def extract_relevant_content(self, content: CrawledContent) -> str:
            raise Exception("Simulated extraction failure")
        
        async def validate_content(self, content: CrawledContent) -> bool:
            return False
    
    return FailedMockCrawler()

@pytest.fixture
def mock_failed_document_interface():
    """Create a mock document interface that simulates failures."""
    class FailedMockDocument:
        async def format_research_results(self, results: Dict[str, Any], template: DocumentTemplate) -> str:
            raise Exception("Simulated formatting failure")
        
        async def generate_document(self, content: str, template: DocumentTemplate) -> bytes:
            raise Exception("Simulated generation failure")
        
        async def validate_template(self, template: DocumentTemplate) -> bool:
            return False
    
    return FailedMockDocument()

@pytest.fixture
def markdown_template() -> DocumentTemplate:
    """Create a markdown template for testing."""
    return DocumentTemplate(
        name="markdown_report",
        format=DocumentFormat.MARKDOWN,
        sections=["summary", "content", "references"],
        metadata={
            "type": "technical_report",
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat()
        }
    )

@pytest.fixture
def html_template() -> DocumentTemplate:
    """Create an HTML template for testing."""
    return DocumentTemplate(
        name="html_report",
        format=DocumentFormat.HTML,
        sections=["header", "body", "footer"],
        metadata={
            "type": "web_report",
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat()
        }
    )

