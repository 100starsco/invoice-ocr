"""
Jobs API endpoints for receiving and processing OCR tasks.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Optional
from rq import Queue
import uuid
import logging

from ..database.redis_client import get_redis_connection
from ..middleware.auth import verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter()

class JobRequest(BaseModel):
    """Request model for creating a new OCR job."""
    image_url: str = Field(..., description="URL of the image to process")
    user_id: str = Field(..., description="LINE user ID")
    message_id: str = Field(..., description="LINE message ID")
    webhook_url: str = Field(..., description="Callback URL for completion notification")

class JobResponse(BaseModel):
    """Response model for job creation."""
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Current job status")
    estimated_time: int = Field(..., description="Estimated processing time in seconds")

class JobStatusResponse(BaseModel):
    """Response model for job status check."""
    job_id: str
    status: str
    progress: Optional[int] = None
    result: Optional[dict] = None
    error: Optional[str] = None

@router.post("/jobs/process-invoice", response_model=JobResponse, dependencies=[Depends(verify_api_key)])
async def create_invoice_job(job_request: JobRequest):
    """
    Create a new invoice processing job.

    Receives job data from Node.js API and queues it for RQ processing.
    The job will be processed asynchronously and results sent via webhook.
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Get Redis connection and create queue
        redis_conn = get_redis_connection()
        queue = Queue('ocr', connection=redis_conn)

        # Import consolidated worker function - processes complete pipeline
        from ..workers.consolidated_invoice_worker import process_invoice_complete_pipeline

        # Enqueue complete invoice processing job
        processing_job = queue.enqueue(
            process_invoice_complete_pipeline,
            job_id,
            job_request.image_url,
            job_request.user_id,
            job_request.message_id,
            job_request.webhook_url,
            None,  # Use default processing config
            job_timeout=300  # 5 minutes for complete pipeline
        )

        # Store job reference for tracking
        rq_job = processing_job

        logger.info(f"Created OCR job {job_id} (RQ job {rq_job.id}) for user {job_request.user_id}")

        return JobResponse(
            job_id=job_id,
            status="queued",
            estimated_time=60
        )

    except Exception as e:
        logger.error(f"Failed to create job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get status of a specific job.

    Optional endpoint for polling job status if webhook fails.
    """
    try:
        redis_conn = get_redis_connection()
        queue = Queue('ocr', connection=redis_conn)

        # Try to find RQ job by searching all jobs
        # Note: This is a simplified approach - in production you'd store job mappings
        jobs = queue.get_jobs()
        rq_job = None

        for job in jobs:
            if job.args and len(job.args) > 0 and job.args[0] == job_id:
                rq_job = job
                break

        if not rq_job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get job status and metadata
        status = rq_job.get_status()
        progress = getattr(rq_job.meta, 'progress', 0) if hasattr(rq_job, 'meta') else 0
        result = rq_job.result if rq_job.is_finished else None
        error = str(rq_job.exc_info) if rq_job.is_failed else None

        return JobStatusResponse(
            job_id=job_id,
            status=status,
            progress=progress,
            result=result,
            error=error
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status for {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@router.get("/jobs", tags=["Jobs"])
async def list_jobs():
    """
    List all jobs in the queue (for debugging/monitoring).
    """
    try:
        redis_conn = get_redis_connection()
        queue = Queue('ocr', connection=redis_conn)

        jobs = queue.get_jobs()
        job_list = []

        for job in jobs:
            job_list.append({
                "rq_job_id": job.id,
                "status": job.get_status(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            })

        return {
            "total_jobs": len(job_list),
            "jobs": job_list
        }

    except Exception as e:
        logger.error(f"Failed to list jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")