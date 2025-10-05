"""
Consolidated Invoice Processing Worker

Single worker that handles the complete invoice processing pipeline:
1. Image preprocessing and enhancement
2. OCR text extraction using PaddleOCR
3. Structured field extraction
4. Results storage in MongoDB
5. Webhook notification

This consolidates the previously problematic two-stage pipeline into a single reliable worker.
"""

import asyncio
import logging
import time
from typing import Dict, Any
from datetime import datetime, timezone

from rq import get_current_job
from ..core.image_processor import ImageProcessor
from ..core.ocr_engine import OCREngine
from ..database.mongodb import MongoDBClient
from ..utils.signatures import generate_webhook_signature
from ..utils.logging_config import log_pipeline_stage, log_webhook_activity
from ..utils.json_utils import prepare_webhook_payload

logger = logging.getLogger(__name__)


def process_invoice_complete_pipeline(
    job_id: str,
    image_url: str,
    user_id: str,
    message_id: str,
    webhook_url: str,
    processing_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Complete invoice processing pipeline in a single worker.

    Processes invoice image from start to finish:
    1. Downloads and preprocesses image
    2. Extracts text using PaddleOCR
    3. Parses structured invoice fields
    4. Stores results in MongoDB
    5. Sends completion webhook

    Args:
        job_id: Unique job identifier
        image_url: URL of original image to process
        user_id: LINE user ID
        message_id: LINE message ID
        webhook_url: Callback URL for completion notification
        processing_config: Configuration for processing operations

    Returns:
        Complete processing results
    """
    job = get_current_job()
    start_time = time.time()

    logger.info(f"Starting complete invoice processing pipeline for job {job_id}")

    # Default processing configuration
    if processing_config is None:
        processing_config = {
            'operations': ['resize', 'crop_invoice', 'denoise', 'enhance_contrast',
                          'perspective_correct', 'deskew', 'sharpen', 'threshold'],
            'max_width': 2048,
            'max_height': 2048,
            'jpeg_quality': 95,
            'fallback_to_original': True,
            'confidence_threshold': 0.3
        }

    try:
        # Initialize job metadata
        job.meta['progress'] = 0
        job.meta['stage'] = 'initializing'
        job.meta['start_time'] = start_time
        job.save_meta()

        logger.info(f"Job {job_id}: ================== PIPELINE START ==================")
        logger.info(f"Job {job_id}: Processing request for user {user_id}")
        logger.info(f"Job {job_id}: Image URL: {image_url[:100]}{'...' if len(image_url) > 100 else ''}")
        logger.info(f"Job {job_id}: Webhook URL: {webhook_url[:100]}{'...' if len(webhook_url) > 100 else ''}")
        logger.info(f"Job {job_id}: Processing config: {processing_config}")

        # === STAGE 1: IMAGE PREPROCESSING ===
        logger.info(f"Job {job_id}: Stage 1 - Image preprocessing")
        job.meta['progress'] = 10
        job.meta['stage'] = 'preprocessing'
        job.save_meta()

        # Initialize image processor
        processor = ImageProcessor()

        # Load and preprocess image
        preprocessing_start = time.time()

        # Download original image
        logger.info(f"Job {job_id}: Downloading image from {image_url[:50]}...")
        try:
            original_image = processor.load_image_from_url(image_url)
            logger.info(f"Job {job_id}: Successfully downloaded image, shape: {original_image.shape if original_image is not None else 'None'}")
        except Exception as download_error:
            logger.error(f"Job {job_id}: Failed to download image: {str(download_error)}")
            logger.error(f"Job {job_id}: Image URL: {image_url}")
            raise ValueError(f"Failed to download image: {str(download_error)}")

        # Check if image contains a document
        logger.info(f"Job {job_id}: Running document classification...")
        try:
            is_document, doc_confidence, doc_metadata = processor.is_document_image(original_image, job_id)
            logger.info(f"Job {job_id}: Document classification result - Is document: {is_document}, Confidence: {doc_confidence:.3f}")
            logger.info(f"Job {job_id}: Document metadata: {doc_metadata}")
        except Exception as classification_error:
            logger.error(f"Job {job_id}: Document classification failed: {str(classification_error)}")
            logger.warning(f"Job {job_id}: Skipping document classification, proceeding with OCR...")
            is_document = True  # Assume it's a document and continue
            doc_confidence = 0.5
            doc_metadata = {"classification_skipped": True, "error": str(classification_error)}

        if not is_document:
            error_msg = f"Image does not contain a document (confidence: {doc_confidence:.3f})"
            logger.error(f"Job {job_id}: {error_msg}")
            raise ValueError(error_msg)

        # Apply preprocessing pipeline
        logger.info(f"Job {job_id}: Applying preprocessing operations: {processing_config.get('operations')}")
        try:
            processed_image, processing_metadata = processor.preprocess_image(
                original_image,
                operations=processing_config.get('operations'),
                job_id=job_id
            )
            logger.info(f"Job {job_id}: Preprocessing completed successfully")
            logger.info(f"Job {job_id}: Applied operations: {processing_metadata.get('operations_applied', [])}")
            logger.info(f"Job {job_id}: Image shape after preprocessing: {processed_image.shape if processed_image is not None else 'None'}")
        except Exception as preprocessing_error:
            logger.error(f"Job {job_id}: Preprocessing failed: {str(preprocessing_error)}")
            logger.warning(f"Job {job_id}: Using original image for OCR...")
            processed_image = original_image
            processing_metadata = {
                'operations_applied': [],
                'preprocessing_failed': True,
                'error': str(preprocessing_error)
            }

        preprocessing_time = time.time() - preprocessing_start
        processing_metadata['preprocessing_time'] = preprocessing_time

        logger.info(f"Job {job_id}: Preprocessing completed in {preprocessing_time:.2f}s")

        # === STAGE 2: OCR TEXT EXTRACTION ===
        logger.info(f"Job {job_id}: Stage 2 - OCR text extraction")
        job.meta['progress'] = 40
        job.meta['stage'] = 'ocr_extraction'
        job.save_meta()

        ocr_start = time.time()

        # Initialize OCR engine
        logger.info(f"Job {job_id}: Initializing PaddleOCR engine...")
        try:
            # Initialize OCR engine with configured language support
            from config import config
            ocr_language = config.ocr.language  # Use configured language (defaults to 'en')
            logger.info(f"Job {job_id}: Initializing OCR engine with language: {ocr_language}")

            ocr_engine = OCREngine(language=ocr_language, use_gpu=config.ocr.use_gpu)
            ocr_engine.initialize()
            logger.info(f"Job {job_id}: OCR engine initialized successfully")
        except Exception as ocr_init_error:
            logger.error(f"Job {job_id}: Failed to initialize OCR engine: {str(ocr_init_error)}")
            raise RuntimeError(f"OCR engine initialization failed: {str(ocr_init_error)}")

        # Extract text regions
        confidence_threshold = processing_config.get('confidence_threshold', 0.3)
        logger.info(f"Job {job_id}: Starting text extraction with confidence threshold: {confidence_threshold}")
        try:
            text_regions = ocr_engine.extract_text(processed_image, confidence_threshold=confidence_threshold)
            logger.info(f"Job {job_id}: Successfully extracted {len(text_regions)} text regions")

            # Log sample text extractions for debugging
            if text_regions:
                logger.info(f"Job {job_id}: Sample text extractions:")
                for i, region in enumerate(text_regions[:5]):  # Show first 5 regions
                    logger.info(f"  [{i+1}] '{region.get('text', '')}' (confidence: {region.get('confidence', 0):.3f})")
            else:
                logger.warning(f"Job {job_id}: No text regions extracted from image!")
        except Exception as text_extraction_error:
            logger.error(f"Job {job_id}: Text extraction failed: {str(text_extraction_error)}")
            text_regions = []  # Continue with empty results

        # === STAGE 3: STRUCTURED FIELD EXTRACTION ===
        job.meta['progress'] = 60
        job.meta['stage'] = 'field_extraction'
        job.save_meta()

        # Extract structured invoice fields
        logger.info(f"Job {job_id}: Extracting structured invoice fields...")
        try:
            invoice_fields = ocr_engine.extract_invoice_fields(processed_image)
            overall_confidence = ocr_engine.calculate_overall_confidence(text_regions)

            logger.info(f"Job {job_id}: Field extraction results:")
            logger.info(f"  Vendor: {invoice_fields.get('vendor', {}).get('value', 'Not found')} (confidence: {invoice_fields.get('vendor', {}).get('confidence', 0):.3f})")
            logger.info(f"  Amount: {invoice_fields.get('total_amount', {}).get('value', 'Not found')} (confidence: {invoice_fields.get('total_amount', {}).get('confidence', 0):.3f})")
            logger.info(f"  Date: {invoice_fields.get('date', {}).get('value', 'Not found')} (confidence: {invoice_fields.get('date', {}).get('confidence', 0):.3f})")
            logger.info(f"  Invoice number: {invoice_fields.get('invoice_number', {}).get('value', 'Not found')} (confidence: {invoice_fields.get('invoice_number', {}).get('confidence', 0):.3f})")
            logger.info(f"  Overall confidence: {overall_confidence:.3f}")
        except Exception as field_extraction_error:
            logger.error(f"Job {job_id}: Field extraction failed: {str(field_extraction_error)}")
            # Use fallback empty structure
            invoice_fields = {
                "vendor": {"value": "Unknown", "confidence": 0.0},
                "total_amount": {"value": 0.0, "confidence": 0.0},
                "date": {"value": "Unknown", "confidence": 0.0},
                "invoice_number": {"value": "Unknown", "confidence": 0.0},
                "line_items": []
            }
            overall_confidence = 0.0

        ocr_time = time.time() - ocr_start
        logger.info(f"Job {job_id}: OCR processing completed in {ocr_time:.2f}s")

        # Cleanup OCR engine
        ocr_engine.cleanup()

        # === STAGE 4: PREPARE RESULTS ===
        job.meta['progress'] = 80
        job.meta['stage'] = 'preparing_results'
        job.save_meta()

        # Build complete result structure
        result_data = {
            "job_id": job_id,
            "user_id": user_id,
            "message_id": message_id,
            "original_image_url": image_url,
            "vendor": invoice_fields.get("vendor", {}).get("value", "Unknown"),
            "amount": invoice_fields.get("total_amount", {}).get("value", 0.0),
            "date": invoice_fields.get("date", {}).get("value", "Unknown"),
            "invoice_number": invoice_fields.get("invoice_number", {}).get("value", "Unknown"),
            "confidence_score": overall_confidence,
            "line_items": [],
            "raw_text_regions": text_regions[:20],  # Limit for storage
            "invoice_fields": invoice_fields,
            "processing_metadata": {
                "preprocessing_applied": processing_metadata.get('operations_applied', []),
                "preprocessing_time": preprocessing_time,
                "ocr_time": ocr_time,
                "total_time": time.time() - start_time,
                "image_quality_improvement": processing_metadata.get('quality_after', {}).get('overall', 0) - processing_metadata.get('quality_before', {}).get('overall', 0),
                "total_text_regions": len(text_regions),
                "ocr_engine_version": "PaddleOCR-2.7+",
                "language_model": "thai+english" if ocr_language == 'th+en' else ocr_language,
                "document_classification": doc_metadata
            }
        }

        # Format line items
        line_items_data = invoice_fields.get("line_items", [])
        for item in line_items_data[:10]:  # Limit to 10 items
            description = item.get("description", {})
            amount = item.get("amount", {})

            result_data["line_items"].append({
                "description": description.get("value", "Unknown"),
                "amount": amount.get("value", 0.0),
                "confidence": min(description.get("confidence", 0.0), amount.get("confidence", 0.0))
            })

        # === STAGE 5: STORE IN DATABASE ===
        logger.info(f"Job {job_id}: Stage 5 - Storing results in database")
        job.meta['progress'] = 90
        job.meta['stage'] = 'storing_results'
        job.save_meta()

        try:
            logger.info(f"Job {job_id}: Storing results in MongoDB...")
            # Store in MongoDB (using async call within sync function)
            asyncio.run(store_results_in_mongodb(job_id, result_data, invoice_fields, text_regions, processing_metadata, start_time))
            logger.info(f"Job {job_id}: Successfully stored results in MongoDB")

        except Exception as db_error:
            logger.error(f"Job {job_id}: Failed to store results in database: {str(db_error)}")
            logger.error(f"Job {job_id}: Database error details: {type(db_error).__name__}: {str(db_error)}")
            # Continue with webhook even if database storage fails

        # === STAGE 6: SEND COMPLETION WEBHOOK ===
        job.meta['progress'] = 95
        job.meta['stage'] = 'sending_webhook'
        job.save_meta()

        # Calculate final processing time
        total_processing_time = time.time() - start_time

        # Prepare webhook payload
        webhook_payload = {
            "event": "job.completed",
            "job_id": job_id,
            "user_id": user_id,
            "message_id": message_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "processing_time": total_processing_time,
            "result": {
                "vendor": result_data["vendor"],
                "amount": result_data["amount"],
                "date": result_data["date"],
                "invoice_number": result_data["invoice_number"],
                "confidence_score": result_data["confidence_score"],
                "invoice_summary": f"{result_data['vendor']} - {result_data['amount']}฿",
                "line_items": result_data["line_items"],
                "ocr_metadata": result_data["processing_metadata"]
            }
        }

        # Send webhook
        logger.info(f"Job {job_id}: Sending completion webhook...")
        try:
            webhook_sent = asyncio.run(send_webhook(webhook_url, webhook_payload))
            if webhook_sent:
                logger.info(f"Job {job_id}: Webhook sent successfully")
            else:
                logger.warning(f"Job {job_id}: Webhook delivery failed, but job completed successfully")
        except Exception as webhook_error:
            logger.error(f"Job {job_id}: Webhook sending failed with exception: {str(webhook_error)}")
            webhook_sent = False

        # === COMPLETION ===
        job.meta['progress'] = 100
        job.meta['stage'] = 'completed'
        job.meta['processing_time'] = total_processing_time
        job.save_meta()

        logger.info(f"Job {job_id}: ================== PIPELINE SUCCESS ==================")
        logger.info(f"Job {job_id}: Complete pipeline finished successfully")
        logger.info(f"Job {job_id}: Performance metrics:")
        logger.info(f"  - Total time: {total_processing_time:.2f}s")
        logger.info(f"  - Preprocessing: {preprocessing_time:.2f}s")
        logger.info(f"  - OCR: {ocr_time:.2f}s")
        logger.info(f"Job {job_id}: Extraction results:")
        logger.info(f"  - Overall confidence: {overall_confidence:.3f}")
        logger.info(f"  - Vendor: {result_data['vendor']}")
        logger.info(f"  - Amount: {result_data['amount']}")
        logger.info(f"  - Date: {result_data['date']}")
        logger.info(f"  - Invoice number: {result_data['invoice_number']}")
        logger.info(f"  - Text regions found: {len(text_regions)}")
        logger.info(f"  - Line items: {len(result_data['line_items'])}")
        logger.info(f"Job {job_id}: =================== PIPELINE END ===================")

        return result_data

    except Exception as e:
        # Handle any errors in the pipeline
        processing_time = time.time() - start_time

        # Update job metadata for failure
        job.meta['stage'] = 'failed'
        job.meta['error'] = str(e)
        job.meta['processing_time'] = processing_time
        job.save_meta()

        logger.error(f"Job {job_id}: ================== PIPELINE FAILED ==================")
        logger.error(f"Job {job_id}: Pipeline failed with error: {str(e)}")
        logger.error(f"Job {job_id}: Error type: {type(e).__name__}")
        logger.error(f"Job {job_id}: Processing time before failure: {processing_time:.2f}s")
        logger.error(f"Job {job_id}: Current stage: {job.meta.get('stage', 'unknown')}")

        # Log stack trace for debugging
        import traceback
        logger.error(f"Job {job_id}: Stack trace:")
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                logger.error(f"Job {job_id}: {line}")

        # Send error webhook
        error_payload = {
            "event": "job.failed",
            "job_id": job_id,
            "user_id": user_id,
            "message_id": message_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "processing_time": processing_time,
            "error": str(e),
            "stage": job.meta.get('stage', 'unknown')
        }

        try:
            logger.info(f"Job {job_id}: Sending error webhook...")
            asyncio.run(send_webhook(webhook_url, error_payload))
            logger.info(f"Job {job_id}: Error webhook sent successfully")
        except Exception as webhook_error:
            logger.error(f"Job {job_id}: Failed to send error webhook: {str(webhook_error)}")
            logger.error(f"Job {job_id}: Webhook error type: {type(webhook_error).__name__}")

        # Re-raise the original exception
        raise


async def store_results_in_mongodb(job_id: str, result_data: Dict[str, Any], invoice_fields: Dict[str, Any],
                                 text_regions: list, processing_metadata: Dict[str, Any], start_time: float) -> None:
    """
    Store OCR results in MongoDB.

    Args:
        job_id: Job identifier
        result_data: Complete result data
        invoice_fields: Extracted invoice fields
        text_regions: Raw text regions from OCR
        processing_metadata: Processing metadata
        start_time: Job start time
    """
    from ..database.mongodb import MongoDBClient
    from config import config

    mongodb_client = MongoDBClient(
        connection_url=config.database.mongodb_uri,
        database_name="ocr_results"
    )

    try:
        await mongodb_client.connect()

        # Prepare data for MongoDB
        mongo_result_data = {
            **result_data,
            "vendor_field": invoice_fields.get("vendor", {}),
            "invoice_number_field": invoice_fields.get("invoice_number", {}),
            "date_field": invoice_fields.get("date", {}),
            "total_amount_field": invoice_fields.get("total_amount", {}),
            "full_text": " ".join([region["text"] for region in text_regions]),
            "preprocessing_operations": processing_metadata.get('operations_applied', []),
            "total_processing_time": time.time() - start_time
        }

        result_id = await mongodb_client.store_ocr_result(job_id, mongo_result_data)
        logger.info(f"Job {job_id}: Stored results in MongoDB: {result_id}")

    finally:
        await mongodb_client.disconnect()


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
    import httpx

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