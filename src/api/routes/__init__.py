"""
API route modules
"""

from .email_routes import email_router
from .person_routes import person_router
from .project_routes import project_router

__all__ = [
    "email_router",
    "person_router", 
    "project_router",
]