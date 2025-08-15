-- Script to grant all permissions to database users
-- Run this as a PostgreSQL superuser (postgres)

-- ============================================
-- PRODUCTION DATABASE (mcp_db)
-- ============================================

-- Connect to the production database
\c mcp_db

-- Grant all privileges on the database
GRANT ALL PRIVILEGES ON DATABASE mcp_db TO mcp_user;

-- Grant all privileges on all tables (existing)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mcp_user;

-- Grant all privileges on all sequences (existing)
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mcp_user;

-- Grant all privileges on all functions (existing)
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO mcp_user;

-- Grant usage and create on schema
GRANT ALL ON SCHEMA public TO mcp_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO mcp_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON SEQUENCES TO mcp_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON FUNCTIONS TO mcp_user;

-- Make mcp_user a superuser (optional - only if you want full admin rights)
-- Uncomment the line below if you want mcp_user to be a superuser
ALTER USER mcp_user WITH SUPERUSER;

-- Grant create database privilege (useful for testing)
ALTER USER mcp_user CREATEDB;

-- ============================================
-- TEST DATABASE (test_mcp_db)
-- ============================================

-- Connect to the test database
\c test_mcp_db

-- Grant all privileges on the database
GRANT ALL PRIVILEGES ON DATABASE test_mcp_db TO test_mcp_user;

-- Grant all privileges on all tables (existing)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO test_mcp_user;

-- Grant all privileges on all sequences (existing)
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO test_mcp_user;

-- Grant all privileges on all functions (existing)
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO test_mcp_user;

-- Grant usage and create on schema
GRANT ALL ON SCHEMA public TO test_mcp_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON TABLES TO test_mcp_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON SEQUENCES TO test_mcp_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT ALL PRIVILEGES ON FUNCTIONS TO test_mcp_user;

ALTER USER test_mcp_user WITH SUPERUSER;

-- Grant create database privilege (useful for testing)
ALTER USER test_mcp_user CREATEDB;

-- ============================================
-- VERIFY PERMISSIONS
-- ============================================

-- Show granted privileges for mcp_user
\c mcp_db
\echo 'Privileges for mcp_user on mcp_db:'
SELECT 
    grantee,
    table_schema,
    table_name,
    privilege_type
FROM information_schema.table_privileges
WHERE grantee = 'mcp_user'
LIMIT 10;

-- Show granted privileges for test_mcp_user
\c test_mcp_db
\echo 'Privileges for test_mcp_user on test_mcp_db:'
SELECT 
    grantee,
    table_schema,
    table_name,
    privilege_type
FROM information_schema.table_privileges
WHERE grantee = 'test_mcp_user'
LIMIT 10;

\echo 'Permissions granted successfully!'