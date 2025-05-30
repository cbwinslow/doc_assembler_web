"""Tests for the topic models."""
import pytest
from datetime import datetime
from uuid import UUID

from airesearch.models.topic import Topic, AnalysisMetrics, ResearchResult

def test_topic_creation(sample_topic: Topic):
    """Test basic topic creation."""
    assert isinstance(sample_topic.id, UUID)
    assert sample_topic.title == "Machine Learning in Python"
    assert len(sample_topic.keywords) == 4
    assert isinstance(sample_topic.created_at, datetime)

def test_topic_validation():
    """Test topic validation rules."""
    # Test minimum title length
    with pytest.raises(ValueError):
        Topic(title="", description="Test description")
    
    # Test maximum title length
    with pytest.raises(ValueError):
        Topic(title="x" * 201, description="Test description")
    
    # Test minimum description length
    with pytest.raises(ValueError):
        Topic(title="Test", description="Short")

def test_keyword_validation():
    """Test keyword validation and normalization."""
    topic = Topic(
        title="Test Topic",
        description="Test description",
        keywords=["  TEST  ", "Python  ", "  MACHINE learning  "]
    )
    assert topic.keywords == ["test", "python", "machine learning"]

def test_metrics_validation(sample_metrics: AnalysisMetrics):
    """Test metrics validation."""
    assert 0 <= sample_metrics.relevance_score <= 1
    assert 0 <= sample_metrics.confidence_score <= 1
    
    # Test invalid scores
    with pytest.raises(ValueError):
        AnalysisMetrics(
            relevance_score=1.5,
            confidence_score=0.5,
            source_quality=0.8,
            coverage_score=0.7
        )

def test_research_result_creation(sample_research_result: ResearchResult):
    """Test research result creation and validation."""
    assert isinstance(sample_research_result.id, UUID)
    assert isinstance(sample_research_result.topic_id, UUID)
    assert len(sample_research_result.keywords) > 0
    assert "main_findings" in sample_research_result.analysis

def test_research_result_metrics_update(
    sample_research_result: ResearchResult,
    sample_metrics: AnalysisMetrics
):
    """Test updating research result metrics."""
    original_updated_at = sample_research_result.updated_at
    sample_research_result.update_metrics(sample_metrics)
    
    assert sample_research_result.metrics == sample_metrics
    assert sample_research_result.updated_at > original_updated_at

