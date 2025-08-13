"""
System monitoring and statistics endpoints
"""

import os
import time
import platform
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.api.dependencies import get_current_user
from .base import get_db

# Create router for system endpoints
system_router = APIRouter(prefix="/system", tags=["System"])


@system_router.get("/info")
async def system_info(
    current_user: dict = Depends(get_current_user)
):
    """Get system information - requires authentication"""
    try:
        # Try to import psutil for system metrics
        import psutil
        
        # Get CPU information
        cpu_info = {
            "count": psutil.cpu_count(),
            "percent": psutil.cpu_percent(interval=1),
            "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else 0
        }
        
        # Get memory information
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        }
        
        # Get disk information
        disk = psutil.disk_usage('/')
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
        
        # Get uptime
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        
    except ImportError:
        # Fallback if psutil is not installed
        cpu_info = {"count": os.cpu_count(), "percent": 0, "frequency": 0}
        memory_info = {"total": 0, "available": 0, "percent": 0, "used": 0}
        disk_info = {"total": 0, "used": 0, "free": 0, "percent": 0}
        uptime_seconds = 0
    
    return {
        "cpu": cpu_info,
        "memory": memory_info,
        "disk": disk_info,
        "uptime": uptime_seconds,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }
    }


@system_router.get("/database/stats")
async def database_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get database statistics - requires authentication"""
    try:
        # Get connection stats
        result = await db.execute(text("""
            SELECT 
                count(*) as total_connections,
                count(*) FILTER (WHERE state = 'active') as active_connections,
                count(*) FILTER (WHERE state = 'idle') as idle_connections
            FROM pg_stat_activity
            WHERE datname = current_database()
        """))
        conn_stats = result.fetchone()
        
        # Get query stats
        result = await db.execute(text("""
            SELECT 
                count(*) as active_queries
            FROM pg_stat_activity
            WHERE state = 'active'
            AND datname = current_database()
        """))
        query_stats = result.fetchone()
        
        # Get table sizes
        result = await db.execute(text("""
            SELECT 
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 10
        """))
        table_sizes = [
            {"schema": row[0], "table": row[1], "size": row[2]}
            for row in result.fetchall()
        ]
        
        return {
            "connections": {
                "total": conn_stats[0] if conn_stats else 0,
                "active": conn_stats[1] if conn_stats else 0,
                "idle": conn_stats[2] if conn_stats else 0
            },
            "active_queries": query_stats[0] if query_stats else 0,
            "table_sizes": table_sizes
        }
    except Exception as e:
        # Return minimal stats if database queries fail
        return {
            "connections": {"total": 1, "active": 1, "idle": 0},
            "active_queries": 0,
            "table_sizes": [],
            "error": str(e)
        }


@system_router.get("/cache/stats")
async def cache_stats(
    current_user: dict = Depends(get_current_user)
):
    """Get cache statistics - requires authentication"""
    # Mock cache stats - in a real app, this would query the cache system
    return {
        "hits": 5000,
        "misses": 500,
        "size": 1024 * 1024 * 10,  # 10MB
        "evictions": 100,
        "hit_ratio": 0.91,
        "entries": 450,
        "max_size": 1024 * 1024 * 100  # 100MB
    }