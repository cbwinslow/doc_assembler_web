"""Tests for the research engine implementation."""
import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

from airesearch.core.researcher import ResearchEngine, ResearchEngineConfig
from airesearch.models.topic import Topic, ResearchResult, AnalysisMetrics

# Core functionality tests
@pytest.mark.asyncio
async def test_research_engine_initialization(engine_config):
    """Test research engine initialization."""
    engine = ResearchEngine(engine_config)
    assert engine.config.model_name == "test-model"
    assert engine.config.max_tokens == 500
    assert isinstance(engine.config.cache_dir, Path)

@pytest.mark.asyncio
async def test_analyze_topic(engine_config, sample_topic, sample_text):
    """Test topic analysis functionality."""
    engine = ResearchEngine(engine_config)
    result = await engine.analyze_topic(sample_topic)
    
    assert isinstance(result, ResearchResult)
    assert result.topic_id == sample_topic.id
    assert len(result.keywords) > 0
    assert isinstance(result.analysis, dict)
    assert len(result.references) >= 0

@pytest.mark.asyncio
async def test_keyword_extraction(engine_config, sample_topic):
    """Test keyword extraction from topic."""
    engine = ResearchEngine(engine_config)
    keywords = await engine._extract_topic_keywords(sample_topic)
    
    assert isinstance(keywords, list)
    assert len(keywords) > 0
    assert all(isinstance(k, str) for k in keywords)
    assert any(k in sample_topic.description.lower() for k in keywords)

@pytest.mark.asyncio
async def test_content_analysis(engine_config, sample_topic):
    """Test content analysis functionality."""
    engine = ResearchEngine(engine_config)
    keywords = ["python", "machine learning"]
    analysis = await engine._analyze_content(sample_topic, keywords)
    
    assert isinstance(analysis, dict)
    assert "main_themes" in analysis
    assert "key_findings" in analysis
    assert "relationships" in analysis
    assert all(isinstance(v, list) for v in analysis.values())

@pytest.mark.asyncio
async def test_content_synthesis(engine_config, sample_research_result):
    """Test content synthesis functionality."""
    engine = ResearchEngine(engine_config)
    results = [sample_research_result]
    content = await engine.synthesize_content(results)
    
    assert isinstance(content, str)
    assert content.strip() != ""

@pytest.mark.asyncio
async def test_reference_gathering(engine_config):
    """Test reference gathering functionality."""
    engine = ResearchEngine(engine_config)
    analysis = {
        "main_themes": ["Theme 1"],
        "key_findings": ["Finding 1"],
        "relationships": []
    }
    
    references = engine._gather_references(analysis)
    assert isinstance(references, list)

@pytest.mark.asyncio
async def test_result_validation(engine_config, sample_topic):
    """Test research result validation."""
    engine = ResearchEngine(engine_config)
    result = await engine.analyze_topic(sample_topic)
    
    assert result.keywords is not None
    assert isinstance(result.keywords, list)
    assert all(isinstance(k, str) for k in result.keywords)
    assert result.created_at <= result.updated_at

@pytest.mark.asyncio
async def test_multiple_topic_analysis(engine_config):
    """Test analysis of multiple topics."""
    engine = ResearchEngine(engine_config)
    topics = [
        Topic(
            title=f"Test Topic {i}",
            description=f"Description for topic {i}",
            keywords=[f"keyword{i}"]
        ) for i in range(3)
    ]
    
    results = []
    for topic in topics:
        result = await engine.analyze_topic(topic)
        results.append(result)
    
    assert len(results) == 3
    assert len({r.id for r in results}) == 3  # All results should be unique

"""Tests for the research engine implementation."""
import pytest
from datetime import datetime
from pathlib import Path

from airesearch.core.researcher import ResearchEngine, ResearchEngineConfig
from airesearch.models.topic import Topic, ResearchResult, AnalysisMetrics

@pytest.mark.asyncio
async def test_analyze_topic(
    engine_config,
    sample_topic,
    sample_text
):
    """Test topic analysis functionality."""
    engine = ResearchEngine(engine_config)
    result = await engine.analyze_topic(sample_topic)
    
    assert isinstance(result, ResearchResult)
    assert result.topic_id == sample_topic.id
    assert len(result.keywords) > 0
    assert isinstance(result.analysis, dict)
    assert len(result.references) >= 0

@pytest.mark.asyncio
async def test_keyword_extraction(
    engine_config,
    sample_topic
):
    """Test keyword extraction from topic."""
    engine = ResearchEngine(engine_config)
    keywords = await engine._extract_topic_keywords(sample_topic)
    
    assert isinstance(keywords, list)
    assert len(keywords) > 0
    assert all(isinstance(k, str) for k in keywords)
    assert any(k in sample_topic.description.lower() for k in keywords)

@pytest.mark.asyncio
async def test_content_analysis(
    engine_config,
    sample_topic
):
    """Test content analysis functionality."""
    engine = ResearchEngine(engine_config)
    keywords = ["python", "machine learning"]
    analysis = await engine._analyze_content(sample_topic, keywords)
    
    assert isinstance(analysis, dict)
    assert "main_themes" in analysis
    assert "key_findings" in analysis
    assert "relationships" in analysis
    assert all(isinstance(v, list) for v in analysis.values())

@pytest.mark.asyncio
async def test_content_synthesis(
    engine_config,
    sample_research_result
):
    """Test content synthesis functionality."""
    engine = ResearchEngine(engine_config)
    results = [sample_research_result]
    content = await engine.synthesize_content(results)
    
    assert isinstance(content, str)

@pytest.mark.asyncio
async def test_invalid_topic_handling(
    engine_config,
    invalid_topic
):
    """Test handling of invalid topics."""
    engine = ResearchEngine(engine_config)
    with pytest.raises(ValueError) as exc_info:
        await engine.analyze_topic(invalid_topic)
    assert "title" in str(exc_info.value).lower()

@pytest.mark.asyncio
async def test_large_result_handling(
    engine_config,
    large_research_result
):
    """Test handling of large research results."""
    engine = ResearchEngine(engine_config)
    results = [large_research_result]
    content = await engine.synthesize_content(results)
    
    assert isinstance(content, str)
    assert len(content) > 0
    assert content.strip() != ""

@pytest.mark.asyncio
async def test_research_depth_config(
    engine_config,
    sample_topic
):
    """Test research depth configuration."""
    results = []
    
    # Test with different depth levels
    for depth in [1, 2, 3]:
        engine_config.research_depth = depth
        engine = ResearchEngine(engine_config)
        result = await engine.analyze_topic(sample_topic)
        results.append(result)
        
        assert isinstance(result, ResearchResult)
        assert len(result.analysis.get("main_themes", [])) >= 0
    
    # Higher depth should potentially yield more insights
    assert len(results) == 3
    for i in range(1, len(results)):
        curr_findings = len(results[i].analysis.get("key_findings", []))
        prev_findings = len(results[i-1].analysis.get("key_findings", []))
        assert curr_findings >= prev_findings

@pytest.mark.asyncio
async def test_caching_behavior(
    engine_config,
    sample_topic,
    tmp_path
):
    """Test caching functionality."""
    # Setup cache directory
    cache_dir = tmp_path / "research_cache"
    cache_dir.mkdir(exist_ok=True)
    engine_config.cache_dir = cache_dir
    
    engine = ResearchEngine(engine_config)
    
    # First analysis
    result1 = await engine.analyze_topic(sample_topic)
    assert result1 is not None
    
    # Second analysis should use cache
    result2 = await engine.analyze_topic(sample_topic)
    assert result2 is not None
    
    assert result1.id == result2.id
    assert result1.keywords == result2.keywords

@pytest.mark.asyncio
async def test_model_configuration(engine_config):
    """Test model configuration handling."""
    # Test different model configurations
    configs = [
        ("gpt-3.5-turbo", 1000, 0.7),
        ("gpt-4", 2000, 0.5),
        ("custom-model", 500, 0.8)
    ]
    
    for model_name, max_tokens, temperature in configs:
        engine_config.model_name = model_name
        engine_config.max_tokens = max_tokens
        engine_config.temperature = temperature
        
        engine = ResearchEngine(engine_config)
        assert engine.config.model_name == model_name
        assert engine.config.max_tokens == max_tokens
        assert engine.config.temperature == temperature

@pytest.mark.asyncio
async def test_concurrent_analysis(
    engine_config,
    sample_topic
):
    """Test concurrent analysis handling."""
    engine = ResearchEngine(engine_config)
    
    # Run multiple analyses concurrently
    tasks = [engine.analyze_topic(sample_topic) for _ in range(3)]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 3
    assert all(isinstance(r, ResearchResult) for r in results)
    # Results should be different due to no caching
    assert len(set(r.id for r in results)) == 3

@pytest.mark.asyncio
async def test_error_handling(engine_config):
    """Test error handling in the research engine."""
    engine = ResearchEngine(engine_config)
    
    # Test with None topic
    with pytest.raises(ValueError):
        await engine.analyze_topic(None)
    
    # Test with empty keywords
    with pytest.raises(ValueError):
        await engine._analyze_content(Topic(
            title="Test",
            description="Test description"
        ), [])
    
    # Test with invalid cache directory
    engine_config.cache_dir = Path("/nonexistent/path")
    engine = ResearchEngine(engine_config)
    # Should handle invalid cache dir gracefully
    assert engine.config.cache_dir.exists() is False

"""Tests for the research engine functionality."""
import pytest
from unittest.mock import Mock
from pathlib import Path

from airesearch.core.researcher import ResearchEngine, ResearchEngineConfig
from airesearch.models.topic import Topic, ResearchResult

@pytest.mark.asyncio
async def test_research_engine_initialization(engine_config: ResearchEngineConfig):
    """Test research engine initialization."""
    engine = ResearchEngine(engine_config)
    assert engine.config.model_name == "test-model"
    assert engine.config.max_tokens == 500
    assert isinstance(engine.config.cache_dir, Path)

@pytest.mark.asyncio
async def test_topic_analysis(engine_config: ResearchEngineConfig, sample_topic: Topic):
    """Test topic analysis functionality."""
    engine = ResearchEngine(engine_config)
    result = await engine.analyze_topic(sample_topic)
    
    assert isinstance(result, ResearchResult)
    assert result.topic_id == sample_topic.id
    assert len(result.keywords) > 0
    assert isinstance(result.analysis, dict)

@pytest.mark.asyncio
async def test_keyword_extraction(engine_config: ResearchEngineConfig, sample_topic: Topic):
    """Test keyword extraction from topic."""
    engine = ResearchEngine(engine_config)
    keywords = await engine._extract_topic_keywords(sample_topic)
    
    assert isinstance(keywords, list)
    assert len(keywords) > 0
    assert all(isinstance(k, str) for k in keywords)

@pytest.mark.asyncio
async def test_content_analysis(engine_config: ResearchEngineConfig, sample_topic: Topic):
    """Test content analysis functionality."""
    engine = ResearchEngine(engine_config)
    keywords = ["python", "machine learning"]
    analysis = await engine._analyze_content(sample_topic, keywords)
    
    assert isinstance(analysis, dict)
    assert "main_themes" in analysis
    assert "key_findings" in analysis
    assert "relationships" in analysis

@pytest.mark.asyncio
async def test_content_synthesis(
    engine_config: ResearchEngineConfig,
    sample_research_result: ResearchResult
):
    """Test content synthesis functionality."""
    engine = ResearchEngine(engine_config)
    content = await engine.synthesize_content([sample_research_result])
    
    assert isinstance(content, str)

@pytest.mark.asyncio
async def test_reference_gathering(engine_config: ResearchEngineConfig):
    """Test reference gathering functionality."""
    engine = ResearchEngine(engine_config)
    analysis = {
        "main_themes": ["Theme 1"],
        "key_findings": ["Finding 1"],
        "relationships": []
    }
    
    references = engine._gather_references(analysis)
    assert isinstance(references, list)

