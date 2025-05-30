"""
FastAPI server implementation for the MCP server.
Provides endpoints for web crawling, research tasks, and LLM consultation.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import psutil
from fastapi import FastAPI, HTTPException, Security, Depends, BackgroundTasks, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl

from ..core.agent import DocumentationAgent, ResearchAgent, AgentConfig
from ..core.crawler import CrawlerConfig, ContentExtraction, PlaywrightCrawler
from ..tools.llm import LLMConsultant
from ..models.database import get_session

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(os.getenv("LOG_DIR", "logs"), "mcp_server.log"))
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MCP Server",
    description="Message Control Program server for AI-powered web crawling and document assembly",
    version="0.1.0"
)

# Security
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """Verify the API key provided in the request."""
    expected_key = os.getenv("MCP_API_KEY")
    if not expected_key:
        logger.error("MCP_API_KEY not configured")
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: API key not configured"
        )
    if api_key != expected_key:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    return api_key

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handling middleware
@app.middleware("http")
async def error_handler(request: Request, call_next):
    """Global error handling middleware."""
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "debug_info": str(e) if os.getenv("SHOW_ERROR_DETAILS", "false").lower() == "true" else None
            }
        )

# Task storage with TTL
tasks: Dict[str, Dict[str, Any]] = {}

# Maximum task retention time (24 hours)
TASK_TTL = int(os.getenv("TASK_TTL", "86400"))

# Models
class TaskStatus(str):
    """Task status enumeration."""
    PENDING = "pending"
    INITIATED = "initiated"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskType(str):
    """Task type enumeration."""
    CRAWL = "crawl"
    RESEARCH = "research"
    CONSULT = "consult"

class CrawlRequest(BaseModel):
    """Request model for web crawling tasks."""
    url: HttpUrl
    depth: int = int(os.getenv("MAX_CRAWL_DEPTH", "3"))
    content_types: List[str] = ["documentation"]
    follow_links: bool = True
    extract_assets: bool = True

class ResearchRequest(BaseModel):
    """Request model for research tasks."""
    topic: str
    tags: List[str]
    depth: str = os.getenv("ANALYSIS_DEPTH", "standard")
    max_sources: int = int(os.getenv("MAX_SOURCES", "10"))
    include_citations: bool = True

class ConsultRequest(BaseModel):
    """Request model for LLM consultation."""
    query: str
    context: Optional[Dict] = None
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "2000"))

class TaskResponse(BaseModel):
    """Response model for task creation."""
    task_id: str
    status: TaskStatus
    message: str
    created_at: datetime
    estimated_completion: Optional[datetime] = None

class HealthCheck(BaseModel):
    """Health check response model."""
    status: str
    version: str
    timestamp: datetime

class SystemStatus(BaseModel):
    """System status response model."""
    status: str
    components: Dict[str, str]
    tasks: Dict[str, int]
    uptime: float
    memory_usage: float
    crawlers_active: int
    queue_size: int

class TaskDetails(BaseModel):
    """Detailed task status response model."""
    task_id: str
    type: TaskType
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(
        status="ok",
        version="0.1.0",
        timestamp=datetime.utcnow()
    )

@app.get("/status", response_model=SystemStatus)
async def system_status():
    """Get detailed system status."""
    # Check component status
    components = {}
    
    # Check database
    try:
        async with get_session() as session:
            await session.execute("SELECT 1")
        components["database"] = "healthy"
    except Exception as e:
        components["database"] = f"unhealthy: {str(e)}"
    
    # Check Playwright
    try:
        config = CrawlerConfig(start_url="https://example.com", max_depth=1, max_pages=1)
        async with PlaywrightCrawler(config) as crawler:
            await crawler.setup()
        components["playwright"] = "healthy"
    except Exception as e:
        components["playwright"] = f"unhealthy: {str(e)}"
    
    # Get process metrics
    process = psutil.Process()
    active_tasks = len([t for t in tasks.values() if t.get("status") == "processing"])
    
    return SystemStatus(
        status="operational",
        components=components,
        tasks={
            "active": len(asyncio.all_tasks()),
            "pending": len([t for t in tasks.values() if t.get("status") == "pending"])
        },
        uptime=process.create_time(),
        memory_usage=process.memory_percent(),
        crawlers_active=active_tasks,
        queue_size=len(tasks)
    )

# Task-related endpoints
@app.post("/api/v1/crawl", response_model=TaskResponse)
async def crawl(
    request: CrawlRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Security(verify_api_key)
):
    """Initiate a crawling task."""
    task_id = f"crawl_{asyncio.get_event_loop().time()}"
    created_at = datetime.utcnow()
    
    config = AgentConfig(
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        analysis_depth=os.getenv("ANALYSIS_DEPTH", "standard")
    )
    
    agent = DocumentationAgent(config)
    await agent.initialize()
    
    tasks[task_id] = {
        "status": "initiated",
        "agent": agent,
        "created_at": created_at,
        "type": "crawl"
    }
    
    background_tasks.add_task(
        execute_crawl_task,
        task_id,
        request
    )
    
    estimated_completion = datetime.utcnow()
    estimated_completion = estimated_completion.replace(
        minute=estimated_completion.minute + int(request.depth * 2)
    )
    
    return TaskResponse(
        task_id=task_id,
        status="initiated",
        message="Crawling task started",
        created_at=created_at,
        estimated_completion=estimated_completion
    )

@app.post("/api/v1/research", response_model=TaskResponse)
async def research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Security(verify_api_key)
):
    """Initiate a research task."""
    task_id = f"research_{asyncio.get_event_loop().time()}"
    created_at = datetime.utcnow()
    
    config = AgentConfig(
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        analysis_depth=request.depth
    )
    
    agent = ResearchAgent(config)
    await agent.initialize()
    
    tasks[task_id] = {
        "status": "initiated",
        "agent": agent,
        "created_at": created_at,
        "type": "research"
    }
    
    background_tasks.add_task(
        execute_research_task,
        task_id,
        request
    )
    
    estimated_completion = datetime.utcnow()
    estimated_completion = estimated_completion.replace(
        minute=estimated_completion.minute + int(len(request.tags) * 5)
    )
    
    return TaskResponse(
        task_id=task_id,
        status="initiated",
        message="Research task started",
        created_at=created_at,
        estimated_completion=estimated_completion
    )

@app.post("/api/v1/consult")
async def consult(
    request: ConsultRequest,
    api_key: str = Security(verify_api_key)
):
    """Consult the LLM for assistance."""
    consultant = LLMConsultant()
    try:
        response = await consultant.get_solution(
            request.query,
            context=request.context
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/status/{task_id}", response_model=TaskDetails)
async def get_status(
    task_id: str,
    api_key: str = Security(verify_api_key)
) -> TaskDetails:
    """Get the detailed status of a task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    return TaskDetails(
        task_id=task_id,
        type=task["type"],
        status=task["status"],
        created_at=task["created_at"],
        completed_at=task.get("completed_at"),
        progress=task.get("progress", 0.0),
        error=task.get("error"),
        result=task.get("result")
    )

# Background tasks
async def execute_crawl_task(task_id: str, request: CrawlRequest) -> None:
    """Execute a crawling task in the background."""
    task = tasks[task_id]
    agent: DocumentationAgent = task["agent"]
    
    try:
        logger.info(f"Starting crawl task {task_id} for URL: {request.url}")
        tasks[task_id]["status"] = "processing"
        
        result = await agent.execute_task({
            "url": str(request.url),
            "depth": request.depth,
            "content_types": request.content_types,
            "follow_links": request.follow_links,
            "extract_assets": request.extract_assets
        })
        
        tasks[task_id].update({
            "status": "completed",
            "result": result,
            "completed_at": datetime.utcnow()
        })
        logger.info(f"Completed crawl task {task_id}")
        
    except Exception as e:
        logger.error(f"Failed crawl task {task_id}: {str(e)}", exc_info=True)
        tasks[task_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.utcnow()
        })

async def execute_research_task(task_id: str, request: ResearchRequest) -> None:
    """Execute a research task in the background."""
    task = tasks[task_id]
    agent: ResearchAgent = task["agent"]
    
    try:
        logger.info(f"Starting research task {task_id} for topic: {request.topic}")
        tasks[task_id]["status"] = "processing"
        
        result = await agent.execute_task({
            "topic": request.topic,
            "tags": request.tags,
            "depth": request.depth,
            "max_sources": request.max_sources,
            "include_citations": request.include_citations
        })
        
        tasks[task_id].update({
            "status": "completed",
            "result": result,
            "completed_at": datetime.utcnow()
        })
        logger.info(f"Completed research task {task_id}")
        
    except Exception as e:
        logger.error(f"Failed research task {task_id}: {str(e)}", exc_info=True)
        tasks[task_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.utcnow()
        })

async def cleanup_old_tasks() -> None:
    """Remove old tasks based on TTL."""
    cleanup_interval: int = int(os.getenv("CLEANUP_INTERVAL", "3600"))  # Default: 1 hour
    
    while True:
        try:
            current_time = datetime.utcnow()
            expired_tasks = [
                task_id for task_id, task in tasks.items()
                if "created_at" in task and
                (current_time - task["created_at"]).total_seconds() > TASK_TTL
            ]
            
            for task_id in expired_tasks:
                logger.info(f"Removing expired task {task_id}")
                tasks.pop(task_id, None)
                
        except Exception as e:
            logger.error(f"Error in task cleanup: {str(e)}", exc_info=True)
            
        await asyncio.sleep(cleanup_interval)

@app.on_event("startup")
async def startup_event():
    """Run startup tasks."""
    logger.info("Starting MCP server")
    asyncio.create_task(cleanup_old_tasks())

@app.on_event("shutdown")
async def shutdown_event():
    """Run shutdown tasks."""
    logger.info("Shutting down MCP server")
    # Add any cleanup tasks here

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=log_level,
        workers=int(os.getenv("WORKERS", "1")),
        reload=os.getenv("ENABLE_HOT_RELOAD", "false").lower() == "true"
    )

