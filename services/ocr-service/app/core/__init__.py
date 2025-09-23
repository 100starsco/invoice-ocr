"""
Core OCR Processing Module

Contains the main OCR engine and image processing functionality.
"""

from .ocr_engine import OCREngine
from .image_processor import ImageProcessor

__all__ = [
    "OCREngine",
    "ImageProcessor",
]