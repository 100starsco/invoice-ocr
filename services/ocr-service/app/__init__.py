"""
OCR Service Application Package

Base package for the FastAPI OCR service providing Thai invoice processing
capabilities using PaddleOCR with queue-based processing.
"""

__version__ = "1.0.0"
__author__ = "Invoice OCR Team"
__description__ = "FastAPI OCR Service for Thai Invoice Processing"

# Package-level imports for easy access
from .core import OCREngine, ImageProcessor
from .models import OCRRequest, OCRResponse, JobStatus
from .database import MongoDBClient, RedisClient

__all__ = [
    "OCREngine",
    "ImageProcessor",
    "OCRRequest",
    "OCRResponse",
    "JobStatus",
    "MongoDBClient",
    "RedisClient",
]