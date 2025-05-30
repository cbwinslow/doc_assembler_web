"""
Task and result models for the MCP server.
"""

from typing import Dict, Optional
from sqlalchemy import Column, String, Integer, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from .database import Base

class TaskStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskType(enum.Enum):
    CRAWL = "crawl"
    RESEARCH = "research"
    DOCUMENT = "document"

class Task(Base):
    """Task model for tracking all operations."""
    
    id = Column(String(36), primary_key=True)
    type = Column(SQLEnum(TaskType), nullable=False)
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    parameters = Column(JSON, nullable=False)
    progress = Column(Integer, nullable=False, default=0)
    error = Column(String, nullable=True)
    
    # Relationships
    results = relationship("TaskResult", back_populates="task", cascade="all, delete-orphan")
    crawl_results = relationship("CrawlResult", back_populates="task", cascade="all, delete-orphan")

class TaskResult(Base):
    """Results of task execution."""
    
    id = Column(String(36), primary_key=True)
    task_id = Column(String(36), ForeignKey('task.id'), nullable=False)
    result_type = Column(String(50), nullable=False)
    data = Column(JSON, nullable=False)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    task = relationship("Task", back_populates="results")

class CrawlResult(Base):
    """Results specifically from crawling operations."""
    
    id = Column(String(36), primary_key=True)
    task_id = Column(String(36), ForeignKey('task.id'), nullable=False)
    url = Column(String(2048), nullable=False)
    title = Column(String(512), nullable=True)
    content_type = Column(String(50), nullable=True)
    content = Column(JSON, nullable=False)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    task = relationship("Task", back_populates="crawl_results")

