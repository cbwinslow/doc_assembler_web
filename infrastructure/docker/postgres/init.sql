-- Initialize PostgreSQL database for Doc Assembler
-- Create pgvector extension for vector similarity search

-- Create the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create additional extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE doc_assembler_dev TO cbwinslow;

-- Create a basic schema if needed
-- This will be handled by the application's migration system

