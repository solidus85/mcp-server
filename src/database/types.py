"""
Custom database types for cross-database compatibility
"""

import json
from typing import Any, Dict, List, Optional
from sqlalchemy import JSON, String, Text, TypeDecorator
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.mutable import MutableDict, MutableList


class JSONType(TypeDecorator):
    """
    A cross-database JSON type that works with both PostgreSQL and SQLite.
    Uses JSONB for PostgreSQL and JSON for SQLite.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(postgresql.JSONB)
        else:
            return dialect.type_descriptor(JSON)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, (dict, list)):
            return value
        return json.loads(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, (dict, list)):
            return value
        return json.loads(value)


class ArrayType(TypeDecorator):
    """
    A cross-database array type that works with both PostgreSQL and SQLite.
    Uses ARRAY for PostgreSQL and JSON for SQLite.
    """
    impl = Text
    cache_ok = True

    def __init__(self, item_type=String, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_type = item_type

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import ARRAY
            return dialect.type_descriptor(ARRAY(self.item_type))
        else:
            # For SQLite and other databases, use JSON
            return dialect.type_descriptor(JSON)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        # For non-PostgreSQL, convert list to JSON
        if isinstance(value, list):
            return value  # JSON type will handle serialization
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        # For non-PostgreSQL, value should already be a list from JSON
        if isinstance(value, str):
            return json.loads(value)
        return value


# Mutable versions for automatic change tracking
MutableJSONType = MutableDict.as_mutable(JSONType)


def get_mutable_array_type(item_type=String):
    """Get a mutable array type for the current database"""
    return MutableList.as_mutable(ArrayType(item_type))


def get_json_type():
    """Get the appropriate JSON type for the current database"""
    return JSONType()


def get_array_type(item_type=String):
    """Get the appropriate array type for the current database"""
    return ArrayType(item_type)