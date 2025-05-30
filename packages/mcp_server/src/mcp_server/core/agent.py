"""
Core agent implementations for documentation and research tasks.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, HttpUrl

from .crawler import PlaywrightCrawler, CrawlerConfig, ContentExtraction
from ..tools.llm import LLMConsultant

logger = logging.getLogger(__name__)

class AgentConfig(BaseModel):
    """Configuration for AI agents."""
    max_retries: int = 3
    analysis_depth: str = "standard"  # standard, deep, shallow
    llm_temperature: float = 0.7
    max_tokens: int = 2000
    batch_size: int = 5
    concurrent_tasks: int = 3

class AgentResult(BaseModel):
    """Base result model for agent operations."""
    success: bool
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    processing_time: float
    completed_at: datetime

class BaseAgent(ABC):
    """Base class for all AI agents."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.llm = LLMConsultant()
        self.start_time: Optional[float] = None
        self.processed_items: Set[str] = set()
        
    async def initialize(self) -> None:
        """Initialize agent resources."""
        self.start_time = asyncio.get_event_loop().time()
        logger.info(f"{self.__class__.__name__} initialized")
    
    async def cleanup(self) -> None:
        """Clean up agent resources."""
        logger.info(f"{self.__class__.__name__} cleanup completed")
    
    @abstractmethod
    async def execute_task(self, parameters: Dict[str, Any]) -> AgentResult:
        """Execute the agent's main task."""
        pass
    
    async def handle_error(self, error: Exception) -> Optional[Dict[str, Any]]:
        """Handle errors with LLM consultation."""
        try:
            solution = await self.llm.get_solution(
                f"Error in {self.__class__.__name__}: {str(error)}"
            )
            return solution
        except Exception as e:
            logger.error(f"Error handling failed: {e}", exc_info=True)
            return None

class DocumentationAgent(BaseAgent):
    """Agent for crawling and processing documentation."""
    
    async def initialize(self) -> None:
        """Initialize documentation agent."""
        await super().initialize()
        self.crawler = PlaywrightCrawler(
            CrawlerConfig(
                start_url="",  # Will be set per task
                max_depth=5,
                max_pages=100,
                content_types=["documentation"]
            )
        )
        await self.crawler.setup()
    
    async def cleanup(self) -> None:
        """Clean up documentation agent resources."""
        await self.crawler.cleanup()
        await super().cleanup()
    
    async def execute_task(self, parameters: Dict[str, Any]) -> AgentResult:
        """Execute documentation crawling and processing task."""
        start_time = asyncio.get_event_loop().time()
        try:
            # Update crawler configuration
            self.crawler.config.start_url = parameters["url"]
            self.crawler.config.max_depth = parameters.get("depth", 5)
            self.crawler.config.content_types = parameters.get("content_types", ["documentation"])
            
            # Crawl and extract content
            results = await self.crawler.crawl()
            
            # Process results with LLM assistance
            processed_results = []
            for content in results:
                try:
                    enhanced_content = await self.enhance_content(content)
                    processed_results.append(enhanced_content)
                except Exception as e:
                    logger.warning(f"Content enhancement failed: {e}")
                    processed_results.append(content)
            
            return AgentResult(
                success=True,
                data={
                    "url": parameters["url"],
                    "documents": processed_results,
                    "stats": {
                        "pages_processed": len(results),
                        "successful_enhancements": len([r for r in processed_results if r.get("enhanced")])
                    }
                },
                metadata={
                    "depth": parameters.get("depth"),
                    "content_types": parameters.get("content_types")
                },
                processing_time=asyncio.get_event_loop().time() - start_time,
                completed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Documentation task failed: {e}", exc_info=True)
            return AgentResult(
                success=False,
                error=str(e),
                processing_time=asyncio.get_event_loop().time() - start_time,
                completed_at=datetime.utcnow()
            )
    
    async def enhance_content(self, content: ContentExtraction) -> Dict[str, Any]:
        """Enhance extracted content using LLM."""
        try:
            # Request content enhancement from LLM
            enhancement = await self.llm.get_solution(
                f"Enhance and structure this documentation content: {content.content[:1000]}..."
            )
            
            return {
                "original": content.dict(),
                "enhanced": enhancement,
                "enhanced_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.warning(f"Content enhancement failed: {e}")
            return {"original": content.dict()}

class ResearchAgent(BaseAgent):
    """Agent for conducting research and compiling information."""
    
    async def initialize(self) -> None:
        """Initialize research agent."""
        await super().initialize()
        self.visited_urls: Set[str] = set()
        self.sources: List[Dict[str, Any]] = []
    
    async def execute_task(self, parameters: Dict[str, Any]) -> AgentResult:
        """Execute research task."""
        start_time = asyncio.get_event_loop().time()
        try:
            topic = parameters["topic"]
            tags = parameters["tags"]
            max_sources = parameters.get("max_sources", 10)
            
            # Generate search queries from tags
            search_queries = await self.generate_search_queries(topic, tags)
            
            # Collect sources
            sources = []
            for query in search_queries:
                if len(sources) >= max_sources:
                    break
                    
                results = await self.search_and_collect(query)
                sources.extend(results)
            
            # Analyze and synthesize results
            synthesis = await self.synthesize_research(
                topic,
                sources[:max_sources],
                parameters.get("include_citations", True)
            )
            
            return AgentResult(
                success=True,
                data={
                    "topic": topic,
                    "synthesis": synthesis,
                    "sources": sources[:max_sources],
                    "stats": {
                        "total_sources": len(sources),
                        "used_sources": min(len(sources), max_sources),
                        "search_queries": search_queries
                    }
                },
                metadata={
                    "tags": tags,
                    "depth": parameters.get("depth"),
                    "include_citations": parameters.get("include_citations")
                },
                processing_time=asyncio.get_event_loop().time() - start_time,
                completed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Research task failed: {e}", exc_info=True)
            return AgentResult(
                success=False,
                error=str(e),
                processing_time=asyncio.get_event_loop().time() - start_time,
                completed_at=datetime.utcnow()
            )
    
    async def generate_search_queries(self, topic: str, tags: List[str]) -> List[str]:
        """Generate optimized search queries from topic and tags."""
        try:
            query_prompt = f"Generate search queries for research on '{topic}' with tags: {', '.join(tags)}"
            response = await self.llm.get_solution(query_prompt)
            
            if isinstance(response, dict) and "queries" in response:
                return response["queries"]
            return [f"{topic} {tag}" for tag in tags]
            
        except Exception as e:
            logger.warning(f"Query generation failed: {e}")
            return [f"{topic} {tag}" for tag in tags]
    
    async def search_and_collect(self, query: str) -> List[Dict[str, Any]]:
        """Search and collect relevant sources."""
        # Implement web search integration here
        # For now, return placeholder data
        return [{
            "url": f"https://example.com/result_{i}",
            "title": f"Result {i} for {query}",
            "snippet": f"Sample content for {query}",
            "relevance_score": 0.8
        } for i in range(3)]
    
    async def synthesize_research(
        self,
        topic: str,
        sources: List[Dict[str, Any]],
        include_citations: bool
    ) -> Dict[str, Any]:
        """Synthesize research results into a coherent document."""
        try:
            synthesis_prompt = (
                f"Synthesize research on '{topic}' from {len(sources)} sources. "
                f"{'Include citations.' if include_citations else ''}"
            )
            
            synthesis = await self.llm.get_solution(synthesis_prompt)
            
            return {
                "content": synthesis.get("content", ""),
                "summary": synthesis.get("summary", ""),
                "citations": synthesis.get("citations", []) if include_citations else [],
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Research synthesis failed: {e}", exc_info=True)
            return {
                "error": "Synthesis failed",
                "raw_sources": sources
            }

