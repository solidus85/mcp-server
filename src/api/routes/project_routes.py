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
project_router.include_router(project_crud_router)
project_router.include_router(project_people_router)
project_router.include_router(project_search_router)
project_router.include_router(project_stats_router)