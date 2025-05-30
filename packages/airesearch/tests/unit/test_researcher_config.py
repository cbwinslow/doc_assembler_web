"""Tests for research engine configuration and error handling."""
import pytest
import asyncio
from pathlib import Path
from typing import List, Dict, Any

from airesearch.core.researcher import ResearchEngine, ResearchEngineConfig
from airesearch.models.topic import Topic, ResearchResult

@pytest.mark.asyncio
async def test_model_configuration(engine_config):
    """Test model configuration handling."""
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
async def test_research_depth_config(engine_config, sample_topic):
    """Test research depth configuration."""
    results: List[ResearchResult] = []
    
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
async def test_caching_behavior(engine_config, sample_topic, tmp_path):
    """Test caching functionality."""
    cache_dir = tmp_path / "research_cache"
    cache_dir.mkdir(exist_ok=True)
    engine_config.cache_dir = cache_dir
    
    engine = ResearchEngine(engine_config)
    
    result1 = await engine.analyze_topic(sample_topic)
    result2 = await engine.analyze_topic(sample_topic)
    
    assert result1.id == result2.id
    assert result1.keywords == result2.keywords
    assert (cache_dir / f"{sample_topic.id}.json").exists()

@pytest.mark.asyncio
async def test_concurrent_analysis(engine_config, sample_topic):
    """Test concurrent analysis handling."""
    engine = ResearchEngine(engine_config)
    
    tasks = [engine.analyze_topic(sample_topic) for _ in range(3)]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 3
    assert all(isinstance(r, ResearchResult) for r in results)
    assert len(set(r.id for r in results)) == 3

@pytest.mark.asyncio
async def test_error_handling(engine_config):
    """Test error handling in the research engine."""
    engine = ResearchEngine(engine_config)
    
    # Test with None topic
    with pytest.raises(ValueError) as exc_info:
        await engine.analyze_topic(None)
    assert "topic" in str(exc_info.value).lower()
    
    # Test with empty keywords
    with pytest.raises(ValueError) as exc_info:
        await engine._analyze_content(
            Topic(title="Test", description="Test description"),
            []
        )
    assert "keywords" in str(exc_info.value).lower()
    
    # Test with invalid cache directory
    engine_config.cache_dir = Path("/nonexistent/path")
    engine = ResearchEngine(engine_config)
    assert engine.config.cache_dir.exists() is False

@pytest.mark.asyncio
async def test_config_validation():
    """Test configuration validation."""
    with pytest.raises(ValueError):
        ResearchEngineConfig(model_name="", max_tokens=0)
    
    with pytest.raises(ValueError):
        ResearchEngineConfig(
            model_name="test-model",
            max_tokens=-1
        )
    
    with pytest.raises(ValueError):
        ResearchEngineConfig(
            model_name="test-model",
            max_tokens=100,
            temperature=2.0
        )

@pytest.mark.asyncio
async def test_cache_directory_creation(tmp_path):
    """Test cache directory creation and handling."""
    config = ResearchEngineConfig(
        model_name="test-model",
        cache_dir=tmp_path / "new_cache"
    )
    
    engine = ResearchEngine(config)
    assert config.cache_dir.exists()
    assert config.cache_dir.is_dir()

