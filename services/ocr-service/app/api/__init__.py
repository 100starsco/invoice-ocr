"""
API Package

Contains FastAPI route definitions, dependencies, and middleware setup.
"""

from .dependencies import get_database, get_redis_client, get_ocr_engine

__all__ = [
    "get_database",
    "get_redis_client",
    "get_ocr_engine",
]