"""
Project management API endpoints - Main router that combines all project sub-routers
"""

from fastapi import APIRouter

# Import all project sub-routers
from .project_crud_routes import project_crud_router
from .project_people_routes import project_people_router
from .project_search_routes import project_search_router
from .project_stats_routes import project_stats_router

# Create main project router with the /projects prefix
project_router = APIRouter(prefix="/projects", tags=["projects"])

# Include all sub-routers
# IMPORTANT: Include routers with specific paths BEFORE routers with path parameters
# to avoid path parameter routes catching specific paths
project_router.include_router(project_search_router)  # Has /search, /test, etc
project_router.include_router(project_stats_router)   # Has /statistics/overview
project_router.include_router(project_people_router)  # Has /{project_id}/people
project_router.include_router(project_crud_router)    # Has /{project_id} - must be last!