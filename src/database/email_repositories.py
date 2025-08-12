"""
Email repositories module - Re-exports all email-related repository classes

This module maintains backward compatibility by re-exporting all repository
classes that were previously defined in this single file.
"""

# Import and re-export all repository classes
from .person_repository import PersonRepository
from .project_repository import ProjectRepository
from .email_repository import EmailRepository
from .email_thread_repository import EmailThreadRepository

__all__ = [
    'PersonRepository',
    'ProjectRepository', 
    'EmailRepository',
    'EmailThreadRepository'
]