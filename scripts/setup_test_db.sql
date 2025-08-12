-- Script to set up test database for MCP Server
-- Run this as a PostgreSQL superuser

-- Drop test database if it exists
DROP DATABASE IF EXISTS test_mcp_db;

-- Drop test user if exists
DROP USER IF EXISTS test_mcp_user;

-- Create test user with password
CREATE USER test_mcp_user WITH PASSWORD 'test_mcp_pass';

-- Create test database
CREATE DATABASE test_mcp_db OWNER test_mcp_user;

-- Grant all privileges on test database to test user
GRANT ALL PRIVILEGES ON DATABASE test_mcp_db TO test_mcp_user;

-- Connect to the test database
\c test_mcp_db

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO test_mcp_user;

-- Enable extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";