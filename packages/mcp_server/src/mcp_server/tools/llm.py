"""
LLM Consultation tool for AI-powered assistance and problem-solving.
Integrates with OpenAI and OpenRouter for enhanced capabilities.
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import aiohttp
import openai
from openai import AsyncOpenAI
import redis.asyncio as redis
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class LLMConfig(BaseModel):
    """Configuration for LLM services."""
    openai_model: str = Field(default="gpt-4")
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openrouter_api_key: str = Field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=2000, gt=0)
    retry_attempts: int = Field(default=3, ge=1)
    retry_delay: float = Field(default=1.0, gt=0.0)
    cache_ttl: int = Field(default=3600, gt=0)  # Cache TTL in seconds
    timeout: float = Field(default=30.0, gt=0.0)

class LLMResponse(BaseModel):
    """Structured response from LLM services."""
    content: str
    source: str  # openai or openrouter
    model: str
    tokens_used: int
    cost: float
    cached: bool = False
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class LLMConsultant:
    """LLM consultation tool with caching and fallback capabilities."""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize LLM consultant with configuration."""
        self.config = config or LLMConfig()
        self.openai_client = AsyncOpenAI(api_key=self.config.openai_api_key)
        self.redis_client = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0")
        )
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def setup(self) -> None:
        """Set up resources and connections."""
        self._session = aiohttp.ClientSession()
        # Test Redis connection
        try:
            await self.redis_client.ping()
        except redis.ConnectionError:
            logger.warning("Redis connection failed, caching disabled")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self._session:
            await self._session.close()
        await self.redis_client.close()
    
    async def get_solution(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> LLMResponse:
        """Get a solution from LLM services with caching and fallback."""
        cache_key = self._generate_cache_key(query, context)
        
        if use_cache:
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                return cached_response
        
        for attempt in range(self.config.retry_attempts):
            try:
                # Try OpenAI first
                response = await self._query_openai(query, context)
                await self._cache_response(cache_key, response)
                return response
            except Exception as e:
                logger.warning(f"OpenAI attempt {attempt + 1} failed: {e}")
                if attempt == self.config.retry_attempts - 1:
                    # Last attempt, try OpenRouter
                    try:
                        response = await self._query_openrouter(query, context)
                        await self._cache_response(cache_key, response)
                        return response
                    except Exception as e_router:
                        logger.error(f"Both LLM services failed: {e_router}")
                        raise
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
    
    async def _query_openai(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Query OpenAI's GPT models."""
        messages = self._prepare_messages(query, context)
        
        async with asyncio.timeout(self.config.timeout):
            response = await self.openai_client.chat.completions.create(
                model=self.config.openai_model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            source="openai",
            model=self.config.openai_model,
            tokens_used=response.usage.total_tokens,
            cost=self._calculate_openai_cost(response.usage.total_tokens),
            generated_at=datetime.utcnow(),
            metadata={"finish_reason": response.choices[0].finish_reason}
        )
    
    async def _query_openrouter(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Query alternative models through OpenRouter."""
        if not self._session:
            await self.setup()
            
        messages = self._prepare_messages(query, context)
        headers = {
            "Authorization": f"Bearer {self.config.openrouter_api_key}",
            "HTTP-Referer": os.getenv("MCP_SERVER_HOST", "https://cloudcurio.cc"),
        }
        
        async with asyncio.timeout(self.config.timeout):
            async with self._session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json={
                    "model": "anthropic/claude-2",  # Fallback to Claude
                    "messages": messages,
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens
                }
            ) as resp:
                response = await resp.json()
        
        return LLMResponse(
            content=response["choices"][0]["message"]["content"],
            source="openrouter",
            model=response["model"],
            tokens_used=response["usage"]["total_tokens"],
            cost=self._calculate_openrouter_cost(response["usage"]["total_tokens"]),
            generated_at=datetime.utcnow(),
            metadata={"finish_reason": response["choices"][0]["finish_reason"]}
        )
    
    def _prepare_messages(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """Prepare messages for LLM consultation."""
        messages = [{
            "role": "system",
            "content": (
                "You are an AI assistant helping with web crawling and document "
                "assembly tasks. Provide clear, actionable solutions and explain "
                "your reasoning when needed."
            )
        }]
        
        if context:
            context_str = json.dumps(context, indent=2)
            messages.append({
                "role": "system",
                "content": f"Context:\n{context_str}"
            })
        
        messages.append({
            "role": "user",
            "content": query
        })
        
        return messages
    
    def _generate_cache_key(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate a unique cache key for the query and context."""
        key_content = f"{query}:{json.dumps(context) if context else ''}"
        return f"llm:solution:{hashlib.sha256(key_content.encode()).hexdigest()}"
    
    async def _get_cached_response(self, cache_key: str) -> Optional[LLMResponse]:
        """Retrieve cached response if available."""
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                response = LLMResponse(**data)
                response.cached = True
                return response
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        return None
    
    async def _cache_response(self, cache_key: str, response: LLMResponse) -> None:
        """Cache the LLM response."""
        try:
            await self.redis_client.setex(
                cache_key,
                self.config.cache_ttl,
                response.json()
            )
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
    
    def _calculate_openai_cost(self, tokens: int) -> float:
        """Calculate cost for OpenAI usage."""
        # GPT-4 pricing (adjust as needed)
        return tokens * 0.00003  # $0.03 per 1K tokens
    
    def _calculate_openrouter_cost(self, tokens: int) -> float:
        """Calculate cost for OpenRouter usage."""
        # Claude pricing through OpenRouter (adjust as needed)
        return tokens * 0.00002  # $0.02 per 1K tokens
    
    async def __aenter__(self) -> 'LLMConsultant':
        """Async context manager entry."""
        await self.setup()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.cleanup()

    async def analyze_error(self, error: Exception) -> LLMResponse:
        """Analyze an error and suggest solutions."""
        query = f"""
        Analyze this error and suggest a solution:
        Error: {str(error)}
        
        Please provide:
        1. Analysis of the error
        2. Potential solutions
        3. Code example if applicable
        """
        
        return await self.get_solution(query)

