"""
Database repositories module - Re-exports all repository classes

This module maintains backward compatibility by re-exporting all repository
classes that were previously defined in this single file.
"""

# Import and re-export all repository classes
from .base_repository import BaseRepository, ModelType
from .user_repository import UserRepository
from .auth_repositories import RoleRepository, ApiKeyRepository, SessionRepository
from .document_repositories import DocumentRepository, TagRepository
from .system_repositories import (
    ToolRepository,
    ResourceRepository,
    QueryRepository,
    AuditLogRepository
)

__all__ = [
    'BaseRepository',
    'ModelType',
    'UserRepository',
    'RoleRepository',
    'ApiKeyRepository',
    'SessionRepository',
    'DocumentRepository',
    'TagRepository',
    'ToolRepository',
    'ResourceRepository',
    'QueryRepository',
    'AuditLogRepository'
]