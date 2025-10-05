"""
OCR Worker with Webhook Integration

Processes invoice images using PaddleOCR and sends results via webhook.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

import httpx
from rq import get_current_job
from ..utils.signatures import generate_webhook_signature

logger = logging.getLogger(__name__)

async def send_webhook(webhook_url: str, payload: Dict[str, Any], max_retries: int = 3) -> bool:
    """
    Send webhook notification with retry logic and signature.

    Args:
        webhook_url: URL to send webhook to
        payload: Webhook payload data
        max_retries: Maximum number of retry attempts

    Returns:
        True if webhook sent successfully, False otherwise
    """
    # Generate webhook signature
    try:
        signature = generate_webhook_signature(payload)
    except ValueError as e:
        logger.warning(f"Unable to generate webhook signature: {e}")
        signature = None

    for attempt in range(max_retries + 1):
        try:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "OCR-Service/1.0"
            }

            # Add signature header if available
            if signature:
                headers["X-Webhook-Signature"] = signature

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                logger.info(f"Webhook sent successfully to {webhook_url} (attempt {attempt + 1})")
                return True

        except httpx.TimeoutException:
            logger.warning(f"Webhook timeout to {webhook_url} (attempt {attempt + 1})")
        except httpx.HTTPStatusError as e:
            logger.warning(f"Webhook HTTP error {e.response.status_code} to {webhook_url} (attempt {attempt + 1})")
        except Exception as e:
            logger.warning(f"Webhook error to {webhook_url} (attempt {attempt + 1}): {str(e)}")

        if attempt < max_retries:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

    logger.error(f"Failed to send webhook to {webhook_url} after {max_retries + 1} attempts")
    return False

def process_invoice_job(
    job_id: str,
    image_url: str,
    user_id: str,
    message_id: str,
    webhook_url: str
) -> Dict[str, Any]:
    """
    Process invoice image with webhook notifications.

    Args:
        job_id: Unique job identifier
        image_url: URL of image to process
        user_id: LINE user ID
        message_id: LINE message ID
        webhook_url: Callback URL for notifications

    Returns:
        Processing results
    """
    job = get_current_job()
    start_time = time.time()

    logger.info(f"Starting OCR job {job_id} for user {user_id}")

    try:
        # Initialize job metadata
        job.meta['progress'] = 0
        job.meta['stage'] = 'initializing'
        job.meta['start_time'] = start_time
        job.save_meta()

        # Stage 1: Enqueue preprocessing job first
        logger.info(f"Job {job_id}: Starting two-stage processing pipeline")
        job.meta['progress'] = 10
        job.meta['stage'] = 'enqueue_preprocessing'
        job.save_meta()

        # Import preprocessing worker
        from .preprocessing_worker import preprocess_invoice_image
        from rq import Queue
        from ..database.redis_client import get_redis_connection

        # Create preprocessing queue
        redis_conn = get_redis_connection()
        preprocessing_queue = Queue('preprocessing', connection=redis_conn)

        # Enqueue preprocessing job
        preprocessing_job = preprocessing_queue.enqueue(
            preprocess_invoice_image,
            job_id + '_preprocess',  # Unique preprocessing job ID
            image_url,
            user_id,
            message_id,
            webhook_url,
            job_timeout=180  # 3 minutes for preprocessing
        )

        logger.info(f"Job {job_id}: Enqueued preprocessing job {preprocessing_job.id}")

        # Wait for preprocessing to complete
        job.meta['progress'] = 30
        job.meta['stage'] = 'waiting_preprocessing'
        job.save_meta()

        # Poll for preprocessing completion (with timeout)
        preprocessing_timeout = 300  # 5 minutes
        polling_start = time.time()

        while time.time() - polling_start < preprocessing_timeout:
            preprocessing_job.refresh()

            if preprocessing_job.is_finished:
                preprocessing_result = preprocessing_job.result
                enhanced_image_url = preprocessing_result.get('enhanced_image_url', image_url)
                break
            elif preprocessing_job.is_failed:
                logger.warning(f"Job {job_id}: Preprocessing failed, using original image")
                enhanced_image_url = image_url
                break

            time.sleep(2)  # Poll every 2 seconds
        else:
            logger.warning(f"Job {job_id}: Preprocessing timed out, using original image")
            enhanced_image_url = image_url

        # Stage 2: OCR Extraction
        logger.info(f"Job {job_id}: Extracting text with OCR")
        job.meta['progress'] = 70
        job.meta['stage'] = 'ocr_extraction'
        job.save_meta()

        # TODO: Implement actual PaddleOCR processing
        # For now, simulate OCR results
        time.sleep(5)

        # Mock OCR results for testing
        ocr_result = {
            "vendor": "ร้านอาหารดีใจ",
            "amount": 245.50,
            "date": "2025-01-15",
            "invoice_number": "INV-2025-001",
            "confidence_score": 0.85,
            "line_items": [
                {"description": "ข้าวผัด", "amount": 120.00, "confidence": 0.9},
                {"description": "น้ำอัดลม", "amount": 25.50, "confidence": 0.8},
                {"description": "ค่าบริการ", "amount": 100.00, "confidence": 0.7}
            ]
        }

        # Stage 4: Parse and structure data
        logger.info(f"Job {job_id}: Parsing invoice data")
        job.meta['progress'] = 90
        job.meta['stage'] = 'parsing'
        job.save_meta()

        # TODO: Implement actual invoice parsing logic
        time.sleep(1)

        # Calculate processing time
        processing_time = time.time() - start_time

        # Complete job
        job.meta['progress'] = 100
        job.meta['stage'] = 'completed'
        job.meta['processing_time'] = processing_time
        job.save_meta()

        # Prepare webhook payload for success
        webhook_payload = {
            "event": "job.completed",
            "job_id": job_id,
            "user_id": user_id,
            "message_id": message_id,
            "timestamp": datetime.utcnow().isoformat(),
            "processing_time": processing_time,
            "result": {
                "vendor": ocr_result["vendor"],
                "amount": ocr_result["amount"],
                "date": ocr_result["date"],
                "invoice_number": ocr_result["invoice_number"],
                "confidence_score": ocr_result["confidence_score"],
                "invoice_summary": f"{ocr_result['vendor']} - {ocr_result['amount']}฿",
                "line_items": ocr_result["line_items"]
            }
        }

        # Send success webhook
        logger.info(f"Job {job_id}: Sending completion webhook")
        webhook_sent = asyncio.run(send_webhook(webhook_url, webhook_payload))

        if not webhook_sent:
            logger.warning(f"Job {job_id}: Webhook delivery failed, but job completed successfully")

        logger.info(f"Job {job_id}: Completed successfully in {processing_time:.2f}s")
        return ocr_result

    except Exception as e:
        # Calculate processing time even for failed jobs
        processing_time = time.time() - start_time

        # Update job metadata for failure
        job.meta['stage'] = 'failed'
        job.meta['error'] = str(e)
        job.meta['processing_time'] = processing_time
        job.save_meta()

        # Prepare webhook payload for failure
        error_payload = {
            "event": "job.failed",
            "job_id": job_id,
            "user_id": user_id,
            "message_id": message_id,
            "timestamp": datetime.utcnow().isoformat(),
            "processing_time": processing_time,
            "error": str(e),
            "stage": job.meta.get('stage', 'unknown')
        }

        # Send error webhook
        logger.error(f"Job {job_id}: Failed with error: {str(e)}")
        try:
            asyncio.run(send_webhook(webhook_url, error_payload))
        except Exception as webhook_error:
            logger.error(f"Job {job_id}: Failed to send error webhook: {str(webhook_error)}")

        # Re-raise the original exception
        raise

# Additional utility functions for actual implementation

def download_image(image_url: str) -> str:
    """
    Download image from URL and return local path.

    TODO: Implement actual image download logic
    """
    pass

def preprocess_image(image_path: str) -> str:
    """
    Preprocess image for better OCR results.

    TODO: Implement actual preprocessing with OpenCV
    - Image sharpening
    - Noise reduction
    - Contrast enhancement
    - Perspective correction
    """
    pass

def extract_text_with_paddle_ocr(image_path: str) -> Dict[str, Any]:
    """
    Extract text using PaddleOCR.

    TODO: Implement actual PaddleOCR integration
    """
    pass

def parse_invoice_data(ocr_text: str) -> Dict[str, Any]:
    """
    Parse OCR text to extract structured invoice data.

    TODO: Implement actual parsing logic with regex/NLP
    """
    pass