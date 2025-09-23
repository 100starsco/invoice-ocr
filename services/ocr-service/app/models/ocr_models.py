"""
OCR-specific Pydantic models

Models for OCR requests, responses, and data structures.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class ProcessingStatus(str, Enum):
    """OCR processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImageFormat(str, Enum):
    """Supported image formats."""
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    TIFF = "tiff"


class TextRegion(BaseModel):
    """Text region with bounding box and confidence."""
    text: str = Field(..., description="Extracted text content")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    bounding_box: List[List[int]] = Field(..., description="Bounding box coordinates")

    class Config:
        schema_extra = {
            "example": {
                "text": "ใบกำกับภาษี",
                "confidence": 0.95,
                "bounding_box": [[100, 50], [200, 50], [200, 80], [100, 80]]
            }
        }


class InvoiceField(BaseModel):
    """Structured invoice field with confidence."""
    field_name: str = Field(..., description="Invoice field name")
    value: Union[str, float, int, None] = Field(..., description="Extracted field value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Field confidence score")
    raw_text: Optional[str] = Field(None, description="Raw extracted text")

    class Config:
        schema_extra = {
            "example": {
                "field_name": "total_amount",
                "value": 1250.00,
                "confidence": 0.92,
                "raw_text": "1,250.00 บาท"
            }
        }


class OCRRequest(BaseModel):
    """OCR processing request model."""
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    image_url: Optional[str] = Field(None, description="URL to image file")
    image_format: ImageFormat = Field(ImageFormat.JPEG, description="Image format")
    preprocessing_options: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Image preprocessing options"
    )
    confidence_threshold: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold"
    )
    extract_invoice_fields: bool = Field(
        True,
        description="Whether to extract structured invoice fields"
    )
    user_id: Optional[str] = Field(None, description="User identifier")

    @validator('image_data', 'image_url')
    def validate_image_source(cls, v, values):
        """Ensure either image_data or image_url is provided."""
        # TODO: Implement validation logic
        return v

    class Config:
        schema_extra = {
            "example": {
                "image_url": "https://example.com/invoice.jpg",
                "image_format": "jpeg",
                "confidence_threshold": 0.7,
                "extract_invoice_fields": True,
                "preprocessing_options": {
                    "enhance_contrast": True,
                    "denoise": True
                }
            }
        }


class OCRResponse(BaseModel):
    """OCR processing response model."""
    job_id: str = Field(..., description="Processing job identifier")
    status: ProcessingStatus = Field(..., description="Processing status")
    text_regions: List[TextRegion] = Field(
        default_factory=list,
        description="All detected text regions"
    )
    invoice_fields: List[InvoiceField] = Field(
        default_factory=list,
        description="Structured invoice fields"
    )
    overall_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Overall extraction confidence"
    )
    processing_time_ms: Optional[int] = Field(
        None,
        description="Processing time in milliseconds"
    )
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        schema_extra = {
            "example": {
                "job_id": "ocr_12345",
                "status": "completed",
                "text_regions": [
                    {
                        "text": "ใบกำกับภาษี",
                        "confidence": 0.95,
                        "bounding_box": [[100, 50], [200, 50], [200, 80], [100, 80]]
                    }
                ],
                "overall_confidence": 0.87,
                "processing_time_ms": 1500
            }
        }