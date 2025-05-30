"""
Crawl data models for the MCP server.
"""

from typing import List, Optional
from sqlalchemy import Column, String, Integer, JSON, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship

from .database import Base

# Association table for page links
page_links = Table(
    'page_links',
    Base.metadata,
    Column('source_id', String(36), ForeignKey('webpage.id'), primary_key=True),
    Column('target_id', String(36), ForeignKey('webpage.id'), primary_key=True)
)

class Webpage(Base):
    """Model for storing crawled webpage data."""
    
    id = Column(String(36), primary_key=True)
    url = Column(String(2048), nullable=False, unique=True)
    domain = Column(String(256), nullable=False, index=True)
    title = Column(String(512), nullable=True)
    content = Column(JSON, nullable=False)  # Stores the main content
    html = Column(String, nullable=True)    # Optional storage of raw HTML
    metadata = Column(JSON, nullable=True)  # Page metadata
    doc_type = Column(String(50), nullable=True)  # Documentation type
    processed = Column(Boolean, default=False)
    
    # Relationships
    outbound_links = relationship(
        'Webpage',
        secondary=page_links,
        primaryjoin=id==page_links.c.source_id,
        secondaryjoin=id==page_links.c.target_id,
        backref='inbound_links'
    )
    assets = relationship("Asset", back_populates="webpage", cascade="all, delete-orphan")

class Asset(Base):
    """Model for storing webpage assets (images, files, etc.)."""
    
    id = Column(String(36), primary_key=True)
    webpage_id = Column(String(36), ForeignKey('webpage.id'), nullable=False)
    url = Column(String(2048), nullable=False)
    asset_type = Column(String(50), nullable=False)  # image, script, stylesheet, etc.
    content_type = Column(String(100), nullable=True)
    size = Column(Integer, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    webpage = relationship("Webpage", back_populates="assets")

class DocumentationStructure(Base):
    """Model for storing documentation structure and relationships."""
    
    id = Column(String(36), primary_key=True)
    webpage_id = Column(String(36), ForeignKey('webpage.id'), nullable=False)
    structure_type = Column(String(50), nullable=False)  # toc, section, chapter, etc.
    title = Column(String(512), nullable=True)
    content = Column(JSON, nullable=False)
    parent_id = Column(String(36), ForeignKey('documentationstructure.id'), nullable=True)
    order = Column(Integer, nullable=False, default=0)
    
    # Relationships
    webpage = relationship("Webpage")
    children = relationship(
        "DocumentationStructure",
        backref="parent",
        remote_side=[id],
        cascade="all, delete-orphan"
    )

