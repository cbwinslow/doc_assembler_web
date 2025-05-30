#!/usr/bin/env python3
"""
Setup script for MCP server initialization.
Handles database setup, migrations, and initial configuration.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

import asyncpg
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.mcp_server.models.database import init_models, engine
from src.mcp_server.core.crawler import PlaywrightCrawler, CrawlerConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_database_connection():
    """Verify database connection and create database if it doesn't exist."""
    try:
        # Get connection parameters from environment
        db_params = {
            'user': os.getenv('POSTGRES_USER', 'mcp'),
            'password': os.getenv('POSTGRES_PASSWORD', 'mcppassword'),
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': 'postgres'  # Connect to default database first
        }

        # Connect to PostgreSQL
        conn = await asyncpg.connect(**db_params)
        
        # Check if our database exists
        target_db = os.getenv('POSTGRES_DB', 'mcpdb')
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            target_db
        )

        if not exists:
            # Create database if it doesn't exist
            await conn.execute(f'CREATE DATABASE "{target_db}"')
            logger.info(f"Created database: {target_db}")

        await conn.close()
        return True

    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

async def verify_playwright_installation():
    """Verify Playwright installation and browser availability."""
    try:
        config = CrawlerConfig(
            start_url="https://example.com",
            max_depth=1,
            max_pages=1
        )
        
        async with PlaywrightCrawler(config) as crawler:
            await crawler.setup()
            logger.info("Playwright installation verified successfully")
            return True
            
    except Exception as e:
        logger.error(f"Playwright verification failed: {e}")
        return False

def run_migrations():
    """Run database migrations using Alembic."""
    try:
        alembic_cfg = Config(str(project_root / "alembic.ini"))
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

async def create_initial_data():
    """Create initial data and configurations in the database."""
    try:
        # Initialize models
        await init_models()
        
        # Add any initial data here
        # For example, default configurations, admin user, etc.
        
        logger.info("Initial data created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create initial data: {e}")
        return False

async def main():
    """Main setup function."""
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = [
        'POSTGRES_USER',
        'POSTGRES_PASSWORD',
        'POSTGRES_DB',
        'POSTGRES_HOST',
        'REDIS_URL'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    # Run setup steps
    steps = [
        ('Database Connection', check_database_connection()),
        ('Playwright Installation', verify_playwright_installation()),
        ('Database Migrations', run_migrations()),
        ('Initial Data', create_initial_data())
    ]
    
    failed_steps = []
    for step_name, coro in steps:
        if asyncio.iscoroutine(coro):
            success = await coro
        else:
            success = coro
            
        if not success:
            failed_steps.append(step_name)
            
    if failed_steps:
        logger.error(f"Setup failed. Failed steps: {failed_steps}")
        sys.exit(1)
    else:
        logger.info("Setup completed successfully")

if __name__ == "__main__":
    asyncio.run(main())

