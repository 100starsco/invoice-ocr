"""
Job management Pydantic models

Models for queue jobs, status tracking, and job management.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class JobType(str, Enum):
    """Job type enumeration."""
    PREPROCESSING = "preprocessing"
    OCR_EXTRACTION = "ocr_extraction"
    FULL_PIPELINE = "full_pipeline"


class JobPriority(str, Enum):
    """Job priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class JobStatus(BaseModel):
    """Job status and progress information."""
    job_id: str = Field(..., description="Unique job identifier")
    job_type: JobType = Field(..., description="Type of processing job")
    status: str = Field(..., description="Current job status")
    progress: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage")
    priority: JobPriority = Field(JobPriority.NORMAL, description="Job priority")

    # Timing information
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(None, description="When job started processing")
    completed_at: Optional[datetime] = Field(None, description="When job completed")

    # Job metadata
    user_id: Optional[str] = Field(None, description="User who submitted the job")
    image_id: Optional[str] = Field(None, description="Associated image identifier")

    # Results and errors
    result_id: Optional[str] = Field(None, description="Result identifier if completed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(0, description="Number of retry attempts")

    # Queue information
    queue_name: str = Field("default", description="Queue name")
    worker_id: Optional[str] = Field(None, description="Worker processing the job")

    class Config:
        schema_extra = {
            "example": {
                "job_id": "job_12345",
                "job_type": "ocr_extraction",
                "status": "processing",
                "progress": 75,
                "priority": "normal",
                "user_id": "user_123",
                "queue_name": "ocr_queue"
            }
        }


class JobRequest(BaseModel):
    """Request to create a new job."""
    job_type: JobType = Field(..., description="Type of job to create")
    priority: JobPriority = Field(JobPriority.NORMAL, description="Job priority")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Job-specific parameters"
    )
    user_id: Optional[str] = Field(None, description="User identifier")
    callback_url: Optional[str] = Field(None, description="Webhook URL for completion")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional job metadata"
    )

    class Config:
        schema_extra = {
            "example": {
                "job_type": "full_pipeline",
                "priority": "normal",
                "parameters": {
                    "image_url": "https://example.com/invoice.jpg",
                    "confidence_threshold": 0.7
                },
                "user_id": "user_123"
            }
        }


class JobResponse(BaseModel):
    """Response after job creation or status query."""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Current status")
    message: str = Field(..., description="Response message")
    estimated_completion: Optional[datetime] = Field(
        None,
        description="Estimated completion time"
    )
    queue_position: Optional[int] = Field(None, description="Position in queue")

    class Config:
        schema_extra = {
            "example": {
                "job_id": "job_12345",
                "status": "queued",
                "message": "Job has been queued for processing",
                "queue_position": 3
            }
        }


class QueueInfo(BaseModel):
    """Queue status and statistics."""
    queue_name: str = Field(..., description="Queue name")
    pending_jobs: int = Field(0, description="Number of pending jobs")
    active_jobs: int = Field(0, description="Number of active jobs")
    completed_jobs: int = Field(0, description="Number of completed jobs")
    failed_jobs: int = Field(0, description="Number of failed jobs")
    active_workers: int = Field(0, description="Number of active workers")

    # Performance metrics
    avg_processing_time: Optional[float] = Field(
        None,
        description="Average processing time in seconds"
    )
    throughput_per_minute: Optional[float] = Field(
        None,
        description="Jobs processed per minute"
    )

    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        description="When statistics were last updated"
    )

    class Config:
        schema_extra = {
            "example": {
                "queue_name": "ocr_queue",
                "pending_jobs": 5,
                "active_jobs": 2,
                "completed_jobs": 1247,
                "failed_jobs": 3,
                "active_workers": 3,
                "avg_processing_time": 12.5,
                "throughput_per_minute": 4.2
            }
        }