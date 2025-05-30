"""
Data models for research topics and results.

This module defines the core data structures used in the research process,
including topic definitions and research results.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, validator

class Topic(BaseModel):
    """Model representing a research topic."""
    
    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    keywords: List[str] = Field(default_factory=list)
    scope: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('keywords')
    def validate_keywords(cls, v: List[str]) -> List[str]:
        """Validate keyword list."""
        return [k.strip().lower() for k in v if k.strip()]

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "title": "AI in Healthcare",
                "description": "Research on applications of AI in healthcare diagnostics",
                "keywords": ["ai", "healthcare", "diagnostics", "machine learning"],
                "scope": {
                    "time_range": "2020-2025",
                    "geographical_focus": "global"
                }
            }
        }

class AnalysisMetrics(BaseModel):
    """Model for storing analysis metrics."""
    
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    source_quality: float = Field(..., ge=0.0, le=1.0)
    coverage_score: float = Field(..., ge=0.0, le=1.0)

class Reference(BaseModel):
    """Model for storing reference information."""
    
    id: UUID = Field(default_factory=uuid4)
    title: str
    url: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    publication_date: Optional[datetime] = None
    relevance_score: float = Field(..., ge=0.0, le=1.0)

class ResearchResult(BaseModel):
    """Model representing research results."""
    
    id: UUID = Field(default_factory=uuid4)
    topic_id: UUID
    keywords: List[str] = Field(default_factory=list)
    analysis: Dict[str, Any] = Field(default_factory=dict)
    references: List[str] = Field(default_factory=list)
    metrics: Optional[AnalysisMetrics] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "topic_id": "123e4567-e89b-12d3-a456-426614174000",
                "keywords": ["ai", "healthcare", "diagnosis"],
                "analysis": {
                    "main_findings": ["Finding 1", "Finding 2"],
                    "trends": ["Trend 1", "Trend 2"],
                    "insights": ["Insight 1", "Insight 2"]
                },
                "references": [
                    "Reference 1",
                    "Reference 2"
                ]
            }
        }

    def update_metrics(self, metrics: AnalysisMetrics) -> None:
        """Update analysis metrics."""
        self.metrics = metrics
        self.updated_at = datetime.utcnow()

