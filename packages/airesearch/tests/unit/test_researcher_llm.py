"""Tests for research engine LLM interactions."""
import pytest
import json
from unittest.mock import AsyncMock, patch
from datetime import datetime
from typing import Dict, Any, Optional

from airesearch.core.researcher import ResearchEngine
from airesearch.models.topic import Topic, ResearchResult

class MockLLMResponse:
    """Mock LLM response for testing."""
    def __init__(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.content = content
        self.created_at = datetime.utcnow()
        self.metadata = metadata or {}

@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    async def mock_completion(*args, **kwargs):
        return MockLLMResponse(
            json.dumps({
                "keywords": ["python", "machine learning", "testing"],
                "analysis": {
                    "main_themes": ["Theme 1"],
                    "key_findings": ["Finding 1"],
                    "relationships": []
                }
            }),
            metadata={"tokens_used": 150}
        )
    
    return AsyncMock(completion=mock_completion)

@pytest.fixture
def mock_streaming_llm_client():
    """Create a mock streaming LLM client."""
    async def mock_stream(*args, **kwargs):
        responses = [
            MockLLMResponse("Part 1"),
            MockLLMResponse("Part 2"),
            MockLLMResponse("Part 3")
        ]
        for response in responses:
            yield response
    
    return AsyncMock(stream=mock_stream)

@pytest.mark.asyncio
async def test_llm_topic_analysis(
    engine_config,
    sample_topic,
    mock_llm_client
):
    """Test topic analysis with mocked LLM."""
    with patch('airesearch.core.researcher.LLMClient', return_value=mock_llm_client):
        engine = ResearchEngine(engine_config)
        result = await engine.analyze_topic(sample_topic)
        
        assert isinstance(result, ResearchResult)
        assert mock_llm_client.completion.called
        assert len(result.keywords) > 0
        
        # Verify call parameters
        call_args = mock_llm_client.completion.call_args
        assert 'max_tokens' in call_args.kwargs
        assert 'temperature' in call_args.kwargs
        assert sample_topic.title in str(call_args.args)

@pytest.mark.asyncio
async def test_llm_content_synthesis(
    engine_config,
    sample_research_result,
    mock_llm_client
):
    """Test content synthesis with mocked LLM."""
    with patch('airesearch.core.researcher.LLMClient', return_value=mock_llm_client):
        engine = ResearchEngine(engine_config)
        content = await engine.synthesize_content([sample_research_result])
        
        assert isinstance(content, str)
        assert mock_llm_client.completion.called
        assert len(content) > 0

@pytest.mark.asyncio
async def test_llm_error_handling(engine_config, sample_topic):
    """Test LLM error handling."""
    error_messages = [
        "Rate limit exceeded",
        "Invalid API key",
        "Service unavailable",
        "Context length exceeded"
    ]
    
    for error_msg in error_messages:
        async def mock_error_completion(*args, **kwargs):
            raise Exception(error_msg)
        
        mock_client = AsyncMock(completion=mock_error_completion)
        
        with patch('airesearch.core.researcher.LLMClient', return_value=mock_client):
            engine = ResearchEngine(engine_config)
            with pytest.raises(Exception) as exc_info:
                await engine.analyze_topic(sample_topic)
            assert error_msg in str(exc_info.value)

@pytest.mark.asyncio
async def test_llm_retry_mechanism(
    engine_config,
    sample_topic,
    mock_llm_client
):
    """Test LLM retry mechanism."""
    call_count = 0
    
    async def mock_retry_completion(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:  # Fail twice
            raise Exception(f"Attempt {call_count} failed")
        return MockLLMResponse("Success after retry")
    
    mock_client = AsyncMock(completion=mock_retry_completion)
    
    with patch('airesearch.core.researcher.LLMClient', return_value=mock_client):
        engine = ResearchEngine(engine_config)
        result = await engine.analyze_topic(sample_topic)
        
        assert isinstance(result, ResearchResult)
        assert call_count == 3
        assert mock_client.completion.call_count == 3

@pytest.mark.asyncio
async def test_llm_response_validation(
    engine_config,
    sample_topic,
    mock_llm_client
):
    """Test LLM response validation."""
    invalid_responses = [
        "",  # Empty response
        "   ",  # Whitespace only
        "Invalid JSON format",  # Non-JSON response
        "{}",  # Empty JSON
        json.dumps({"invalid_key": "missing required fields"}),  # Missing required fields
        json.dumps({"keywords": None, "analysis": {}}),  # Invalid data types
    ]
    
    for response in invalid_responses:
        mock_client = AsyncMock(
            completion=AsyncMock(return_value=MockLLMResponse(response))
        )
        
        with patch('airesearch.core.researcher.LLMClient', return_value=mock_client):
            engine = ResearchEngine(engine_config)
            with pytest.raises((ValueError, json.JSONDecodeError)):
                await engine.analyze_topic(sample_topic)

@pytest.mark.asyncio
async def test_llm_token_management(
    engine_config,
    sample_topic,
    mock_llm_client
):
    """Test LLM token management."""
    tracked_tokens = []
    max_token_limit = engine_config.max_tokens
    
    async def mock_token_completion(*args, **kwargs):
        tokens = kwargs.get('max_tokens', 0)
        tracked_tokens.append(tokens)
        return MockLLMResponse(
            "Response with token tracking",
            metadata={"tokens_used": tokens}
        )
    
    mock_client = AsyncMock(completion=mock_token_completion)
    
    with patch('airesearch.core.researcher.LLMClient', return_value=mock_client):
        engine = ResearchEngine(engine_config)
        await engine.analyze_topic(sample_topic)
        
        assert all(t <= max_token_limit for t in tracked_tokens)
        assert len(tracked_tokens) > 0

@pytest.mark.asyncio
async def test_llm_streaming_response(
    engine_config,
    sample_topic,
    mock_streaming_llm_client
):
    """Test handling of streaming LLM responses."""
    with patch('airesearch.core.researcher.LLMClient', return_value=mock_streaming_llm_client):
        engine = ResearchEngine(engine_config)
        result = await engine.analyze_topic(sample_topic, stream=True)
        
        assert isinstance(result, ResearchResult)
        assert mock_streaming_llm_client.stream.called

@pytest.mark.asyncio
async def test_llm_context_handling(
    engine_config,
    sample_topic,
    mock_llm_client
):
    """Test LLM context handling."""
    contexts = []
    
    async def mock_context_completion(*args, **kwargs):
        contexts.append(args[0] if args else "")
        return MockLLMResponse("Test response")
    
    mock_client = AsyncMock(completion=mock_context_completion)
    
    with patch('airesearch.core.researcher.LLMClient', return_value=mock_client):
        engine = ResearchEngine(engine_config)
        await engine.analyze_topic(sample_topic)
        
        assert len(contexts) > 0
        for context in contexts:
            assert sample_topic.title in context or sample_topic.description in context

