"""
Email management API endpoints - Main router that combines all email sub-routers
"""

from fastapi import APIRouter

# Import all email sub-routers
from .email_ingestion_routes import email_ingestion_router
from .email_crud_routes import email_crud_router  
from .email_bulk_routes import email_bulk_router
from .email_stats_routes import email_stats_router

# Create main email router with the /emails prefix
email_router = APIRouter(prefix="/emails", tags=["emails"])

# Include all sub-routers
# Order matters! More specific routes must come before generic ones
email_router.include_router(email_ingestion_router)
email_router.include_router(email_bulk_router)  # Must come before crud_router (which has /{email_id})
email_router.include_router(email_stats_router)
email_router.include_router(email_crud_router)  # This has /{email_id} so must come last