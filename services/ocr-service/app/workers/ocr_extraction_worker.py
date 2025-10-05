"""
OCR Extraction Worker

Stage 2 of the two-stage processing pipeline.
Handles text extraction using PaddleOCR after image preprocessing is complete.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any

import httpx
from rq import get_current_job
from ..utils.signatures import generate_webhook_signature
from ..core.image_processor import ImageProcessor
from ..utils.logging_config import log_pipeline_stage, log_webhook_activity
from ..utils.json_utils import prepare_webhook_payload
from ..utils.url_converter import convert_to_proxy_url

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
    # Prepare payload to ensure JSON serializability
    json_safe_payload = prepare_webhook_payload(payload)

    # Generate webhook signature
    try:
        signature = generate_webhook_signature(json_safe_payload)
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
                    json=json_safe_payload,
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


def extract_invoice_text(
    job_id: str,
    enhanced_image_url: str,
    user_id: str,
    message_id: str,
    webhook_url: str,
    preprocessing_metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Extract text from preprocessed invoice image using PaddleOCR.

    This is Stage 2 of the two-stage processing pipeline.

    Args:
        job_id: Unique OCR job identifier
        enhanced_image_url: URL of preprocessed/enhanced image
        user_id: LINE user ID
        message_id: LINE message ID
        webhook_url: Callback URL for completion notification
        preprocessing_metadata: Metadata from preprocessing stage

    Returns:
        OCR extraction results
    """
    job = get_current_job()
    start_time = time.time()

    logger.info(f"Starting OCR extraction job {job_id} for user {user_id}")

    if preprocessing_metadata is None:
        preprocessing_metadata = {}

    try:
        # Initialize job metadata
        job.meta['progress'] = 0
        job.meta['stage'] = 'initializing'
        job.meta['start_time'] = start_time
        job.save_meta()

        # Stage 1: Download enhanced image using proxy URL
        proxy_url = convert_to_proxy_url(enhanced_image_url)
        log_pipeline_stage(logger, job_id, "loading enhanced image", 10, f"URL: {proxy_url[:50]}...")
        logger.info(f"Job {job_id}: Converting {enhanced_image_url[:50]}... to proxy URL: {proxy_url[:50]}...")
        job.meta['progress'] = 10
        job.meta['stage'] = 'loading_image'
        job.save_meta()

        # Load the enhanced image for OCR using proxy URL
        processor = ImageProcessor()
        enhanced_image = processor.load_image_from_url(proxy_url)

        # Stage 2: PaddleOCR Text Extraction
        logger.info(f"Job {job_id}: Extracting text with PaddleOCR")
        job.meta['progress'] = 40
        job.meta['stage'] = 'ocr_extraction'
        job.save_meta()

        # Initialize OCR engine
        from ..core.ocr_engine import OCREngine

        try:
            # Create and initialize OCR engine with bilingual support
            from config import config
            ocr_language = config.ocr.language  # Use configured language (defaults to 'en')
            logger.info(f"Job {job_id}: Initializing OCR engine with language: {ocr_language}")

            ocr_engine = OCREngine(
                language=ocr_language,
                use_gpu=config.ocr.use_gpu,
                dual_pass=config.ocr.dual_pass
            )
            ocr_engine.initialize()

            logger.info(f"Job {job_id}: OCR engine initialized successfully")

            # Extract text regions using PaddleOCR with enhanced logging
            logger.info(f"Job {job_id}: Starting PaddleOCR text extraction with confidence threshold 0.3")
            logger.info(f"Job {job_id}: Enhanced image shape: {enhanced_image.shape}")

            text_regions = ocr_engine.extract_text(enhanced_image, confidence_threshold=0.3)

            # Detailed text region analysis
            logger.info(f"Job {job_id}: ✓ Extracted {len(text_regions)} total text regions")

            if text_regions:
                high_conf_regions = [r for r in text_regions if r['confidence'] >= 0.7]
                medium_conf_regions = [r for r in text_regions if 0.3 <= r['confidence'] < 0.7]
                low_conf_regions = [r for r in text_regions if r['confidence'] < 0.3]

                logger.info(f"Job {job_id}: Text regions by confidence:")
                logger.info(f"  • High confidence (≥0.7): {len(high_conf_regions)} regions")
                logger.info(f"  • Medium confidence (0.3-0.7): {len(medium_conf_regions)} regions")
                logger.info(f"  • Low confidence (<0.3): {len(low_conf_regions)} regions")

                # Calculate text density
                total_chars = sum(len(r['text']) for r in text_regions)
                logger.info(f"Job {job_id}: Total extracted characters: {total_chars}")
            else:
                logger.warning(f"Job {job_id}: ⚠ NO TEXT REGIONS EXTRACTED - this indicates a critical OCR failure")
                logger.warning(f"Job {job_id}: Enhanced image may be corrupted or OCR engine failed")

            # Extract structured invoice fields
            job.meta['progress'] = 60
            job.meta['stage'] = 'field_extraction'
            job.save_meta()

            logger.info(f"Job {job_id}: Starting structured invoice field extraction")
            invoice_fields = ocr_engine.extract_invoice_fields(enhanced_image)

            # Log detailed field extraction results
            logger.info(f"Job {job_id}: ✓ Invoice field extraction completed")
            for field_name, field_data in invoice_fields.items():
                if field_name == 'line_items':
                    logger.info(f"  • {field_name}: {len(field_data)} items extracted")
                else:
                    value = field_data.get('value')
                    confidence = field_data.get('confidence', 0)
                    status = '✓' if confidence >= 0.5 else '⚠' if confidence >= 0.2 else '✗'
                    logger.info(f"  • {field_name}: {status} '{value}' (confidence: {confidence:.2f})")

            # Calculate overall confidence
            overall_confidence = ocr_engine.calculate_overall_confidence(text_regions)

            # Build OCR result structure
            ocr_result = {
                "vendor": invoice_fields.get("vendor", {}).get("value", "Unknown"),
                "amount": invoice_fields.get("total_amount", {}).get("value", 0.0),
                "date": invoice_fields.get("date", {}).get("value", "Unknown"),
                "invoice_number": invoice_fields.get("invoice_number", {}).get("value", "Unknown"),
                "confidence_score": overall_confidence,
                "line_items": [],
                "raw_text_regions": text_regions[:20],  # Limit to first 20 regions
                "invoice_fields": invoice_fields,  # Detailed field extraction results
                "processing_metadata": {
                    "preprocessing_applied": preprocessing_metadata.get('operations_applied', []),
                    "image_quality_improvement": preprocessing_metadata.get('quality_after', {}).get('overall', 0) - preprocessing_metadata.get('quality_before', {}).get('overall', 0),
                    "enhanced_image_used": True,
                    "total_text_regions": len(text_regions),
                    "ocr_engine_version": "PaddleOCR-2.7+",
                    "language_model": "thai+english" if preprocessing_metadata.get('ocr_language', 'en') == 'en' else preprocessing_metadata.get('ocr_language', 'en')
                }
            }

            # Format line items from field extraction
            line_items_data = invoice_fields.get("line_items", [])
            for item in line_items_data[:10]:  # Limit to 10 items
                description = item.get("description", {})
                amount = item.get("amount", {})

                ocr_result["line_items"].append({
                    "description": description.get("value", "Unknown"),
                    "amount": amount.get("value", 0.0),
                    "confidence": min(description.get("confidence", 0.0), amount.get("confidence", 0.0))
                })

            # Cleanup OCR engine
            ocr_engine.cleanup()

            # Comprehensive completion logging
            logger.info(f"Job {job_id}: 🏆 OCR PROCESSING COMPLETED SUCCESSFULLY")

            # Confidence analysis
            if overall_confidence >= 0.8:
                conf_level = "HIGH"
                conf_emoji = "🟢"
            elif overall_confidence >= 0.5:
                conf_level = "MEDIUM"
                conf_emoji = "🟡"
            else:
                conf_level = "LOW"
                conf_emoji = "🔴"

            logger.info(f"Job {job_id}: {conf_emoji} Overall confidence: {overall_confidence:.3f} ({conf_level})")
            logger.info(f"Job {job_id}: 📊 Extraction summary:")
            logger.info(f"  • Vendor: '{ocr_result['vendor']}'")
            logger.info(f"  • Amount: {ocr_result['amount']}")
            logger.info(f"  • Date: '{ocr_result['date']}'")
            logger.info(f"  • Invoice #: '{ocr_result['invoice_number']}'")
            logger.info(f"  • Text regions: {len(text_regions)}")
            logger.info(f"  • Line items: {len(ocr_result['line_items'])}")

            # Check for critical missing fields
            critical_fields = ['vendor', 'amount']
            missing_critical = [f for f in critical_fields if not ocr_result.get(f) or ocr_result.get(f) in ['Unknown', 0.0]]
            if missing_critical:
                logger.warning(f"Job {job_id}: ⚠ Critical fields missing/empty: {', '.join(missing_critical)}")

        except Exception as ocr_error:
            logger.error(f"Job {job_id}: OCR processing failed: {str(ocr_error)}")

            # Fallback to basic result on OCR failure
            preprocessing_quality = preprocessing_metadata.get('quality_after', {})
            fallback_confidence = preprocessing_quality.get('overall', 0.3)

            ocr_result = {
                "vendor": "OCR Failed",
                "amount": 0.0,
                "date": "Unknown",
                "invoice_number": "Unknown",
                "confidence_score": fallback_confidence,
                "line_items": [],
                "raw_text_regions": [],
                "invoice_fields": {},
                "processing_metadata": {
                    "preprocessing_applied": preprocessing_metadata.get('operations_applied', []),
                    "image_quality_improvement": preprocessing_quality.get('overall', 0) - preprocessing_metadata.get('quality_before', {}).get('overall', 0),
                    "enhanced_image_used": True,
                    "ocr_error": str(ocr_error),
                    "fallback_used": True
                }
            }

            logger.warning(f"Job {job_id}: Using fallback OCR result due to processing error")

        # Stage 3: Parse and structure invoice data
        logger.info(f"Job {job_id}: Parsing invoice data")
        job.meta['progress'] = 80
        job.meta['stage'] = 'parsing'
        job.save_meta()

        # TODO: Implement actual invoice parsing logic
        time.sleep(1)

        # Calculate processing time
        processing_time = time.time() - start_time

        # Include total processing time (preprocessing + OCR)
        total_processing_time = processing_time + preprocessing_metadata.get('preprocessing_time', 0)

        # Complete job
        job.meta['progress'] = 100
        job.meta['stage'] = 'completed'
        job.meta['processing_time'] = processing_time
        job.save_meta()

        # Prepare webhook payload for success
        webhook_payload = {
            "event": "job.completed",
            "job_id": preprocessing_metadata.get('original_job_id', job_id),  # Use original job ID
            "user_id": user_id,
            "message_id": message_id,
            "timestamp": datetime.utcnow().isoformat(),
            "processing_time": total_processing_time,
            "result": {
                "vendor": ocr_result["vendor"],
                "amount": ocr_result["amount"],
                "date": ocr_result["date"],
                "invoice_number": ocr_result["invoice_number"],
                "confidence_score": ocr_result["confidence_score"],
                "invoice_summary": f"{ocr_result['vendor']} - {ocr_result['amount']}฿",
                "line_items": ocr_result["line_items"],
                "preprocessing_metadata": preprocessing_metadata,
                "ocr_metadata": ocr_result["processing_metadata"]
            }
        }

        # Send success webhook
        log_pipeline_stage(logger, job_id, "sending completion webhook", 100)
        start_webhook_time = time.time()
        webhook_sent = asyncio.run(send_webhook(webhook_url, webhook_payload))
        webhook_time = time.time() - start_webhook_time

        log_webhook_activity(
            logger, "job.completed", webhook_url, job_id,
            webhook_sent, webhook_time
        )

        if not webhook_sent:
            logger.warning(f"Job {job_id}: Webhook delivery failed, but job completed successfully")

        logger.info(f"Job {job_id}: OCR extraction completed successfully in {processing_time:.2f}s")
        logger.info(f"Total pipeline time: {total_processing_time:.2f}s")
        logger.info(f"Final confidence score: {ocr_result['confidence_score']:.3f}")

        return ocr_result

    except Exception as e:
        # Calculate processing time even for failed jobs
        processing_time = time.time() - start_time
        total_processing_time = processing_time + preprocessing_metadata.get('preprocessing_time', 0)

        # Update job metadata for failure
        job.meta['stage'] = 'failed'
        job.meta['error'] = str(e)
        job.meta['processing_time'] = processing_time
        job.save_meta()

        # Prepare webhook payload for failure
        error_payload = {
            "event": "job.failed",
            "job_id": preprocessing_metadata.get('original_job_id', job_id),
            "user_id": user_id,
            "message_id": message_id,
            "timestamp": datetime.utcnow().isoformat(),
            "processing_time": total_processing_time,
            "error": str(e),
            "stage": job.meta.get('stage', 'unknown'),
            "preprocessing_metadata": preprocessing_metadata
        }

        # Send error webhook
        logger.error(f"Job {job_id}: OCR extraction failed with error: {str(e)}")
        try:
            asyncio.run(send_webhook(webhook_url, error_payload))
        except Exception as webhook_error:
            logger.error(f"Job {job_id}: Failed to send error webhook: {str(webhook_error)}")

        # Re-raise the original exception
        raise