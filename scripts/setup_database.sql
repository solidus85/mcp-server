-- Database setup script for MCP Server
-- Run this as the postgres superuser:
-- sudo -u postgres psql -d mcp_db -f scripts/setup_database.sql

-- Grant necessary permissions to the mcp_user
GRANT ALL ON SCHEMA public TO mcp_user;
GRANT CREATE ON SCHEMA public TO mcp_user;

-- Ensure the user owns the schema
ALTER SCHEMA public OWNER TO mcp_user;

-- Grant all privileges on the database
GRANT ALL PRIVILEGES ON DATABASE mcp_db TO mcp_user;

-- Grant usage and create on the public schema
GRANT USAGE, CREATE ON SCHEMA public TO mcp_user;

-- Make mcp_user able to create types (enums)
GRANT CREATE ON DATABASE mcp_db TO mcp_user;

-- Display confirmation
\echo 'Database permissions configured for mcp_user'