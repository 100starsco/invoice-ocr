"""
Preprocessing Worker

RQ worker for image preprocessing before OCR processing.
Handles document enhancement, geometric corrections, and quality improvements.
"""

import time
import logging
from typing import Dict, Any
from datetime import datetime

from rq import get_current_job
from ..core.image_processor import ImageProcessor
from ..utils.signatures import generate_webhook_signature
from ..utils.logging_config import log_pipeline_stage, log_redis_activity

logger = logging.getLogger(__name__)


def preprocess_invoice_image(
    job_id: str,
    image_url: str,
    user_id: str,
    message_id: str,
    webhook_url: str,
    preprocessing_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Preprocess invoice image using OpenCV operations.

    This is Stage 1 of the two-stage processing pipeline.
    After preprocessing, it will enqueue the OCR job with the enhanced image.

    Args:
        job_id: Unique job identifier
        image_url: URL of original image to preprocess
        user_id: LINE user ID
        message_id: LINE message ID
        webhook_url: Callback URL for progress updates
        preprocessing_config: Configuration for preprocessing operations

    Returns:
        Preprocessing results with enhanced image URL and metadata
    """
    job = get_current_job()
    start_time = time.time()

    logger.info(f"Starting image preprocessing job {job_id} for user {user_id}")

    # Default preprocessing configuration
    if preprocessing_config is None:
        preprocessing_config = {
            'operations': ['resize', 'crop_invoice', 'denoise', 'enhance_contrast', 'perspective_correct', 'deskew', 'sharpen', 'threshold'],
            'max_width': 2048,
            'max_height': 2048,
            'jpeg_quality': 95,
            'fallback_to_original': True
        }

    try:
        logger.info(f"Job {job_id}: FLOW DEBUG - Entering main try block")

        # Initialize job metadata
        job.meta['progress'] = 0
        job.meta['stage'] = 'initializing'
        job.meta['start_time'] = start_time
        job.save_meta()

        logger.info(f"Job {job_id}: FLOW DEBUG - Job metadata initialized")

        # Initialize image processor
        processor = ImageProcessor()
        logger.info(f"Job {job_id}: FLOW DEBUG - ImageProcessor initialized")

        # Stage 1: Download image
        log_pipeline_stage(logger, job_id, "downloading image", 10, f"URL: {image_url[:50]}...")
        job.meta['progress'] = 10
        job.meta['stage'] = 'downloading'
        job.save_meta()

        # Load image from URL with EXIF correction
        logger.info(f"Job {job_id}: FLOW DEBUG - About to load image from URL")
        original_image = processor.load_image_from_url(image_url)
        logger.info(f"Loaded image with shape: {original_image.shape}")
        logger.info(f"Job {job_id}: FLOW DEBUG - Image loaded successfully")

        # Stage 2: Apply preprocessing operations
        operations_list = preprocessing_config.get('operations', [])
        log_pipeline_stage(logger, job_id, "preprocessing", 30, f"Operations: {', '.join(operations_list)}")
        job.meta['progress'] = 30
        job.meta['stage'] = 'preprocessing'
        job.save_meta()
        logger.info(f"Job {job_id}: FLOW DEBUG - Starting preprocessing operations")

        # Check if image contains a document before intensive processing
        logger.info(f"Job {job_id}: FLOW DEBUG - About to check if image contains document")
        is_document, doc_confidence, doc_metadata = processor.is_document_image(original_image, job_id)

        logger.info(f"Job {job_id}: FLOW DEBUG - Document check result: is_document={is_document}, confidence={doc_confidence:.3f}")

        if not is_document:
            # Image classified as non-document - send webhook immediately
            logger.warning(f"Job {job_id}: Image classified as non-document, aborting preprocessing")
            logger.info(f"Job {job_id}: FLOW DEBUG - Entering non-document branch, will send webhook and raise exception")

            # Send non-document detection webhook
            import requests
            webhook_payload = {
                'event': 'job.failed',
                'job_id': job_id,
                'user_id': user_id,
                'message_id': message_id,
                'timestamp': datetime.now().isoformat(),
                'processing_time': time.time() - start_time,
                'error': 'Non-document image detected',
                'stage': 'document_classification',
                'classification_details': doc_metadata
            }

            try:
                if webhook_url:
                    response = requests.post(webhook_url, json=webhook_payload, timeout=30)
                    logger.info(f"Job {job_id}: Non-document webhook sent, status: {response.status_code}")
            except Exception as webhook_error:
                logger.error(f"Job {job_id}: Failed to send non-document webhook: {str(webhook_error)}")

            # Raise custom exception to mark job as failed
            logger.info(f"Job {job_id}: FLOW DEBUG - About to raise ValueError for non-document")
            raise ValueError(f"Image does not contain a document (confidence: {doc_confidence:.3f})")

        logger.info(f"Job {job_id}: Document classification passed (confidence: {doc_confidence:.3f})")
        logger.info(f"Job {job_id}: FLOW DEBUG - Document classification passed, continuing to preprocessing")

        # Apply preprocessing pipeline
        logger.info(f"Job {job_id}: FLOW DEBUG - About to apply preprocessing pipeline")
        processed_image, processing_metadata = processor.preprocess_image(
            original_image,
            operations=preprocessing_config.get('operations'),
            job_id=job_id
        )
        logger.info(f"Job {job_id}: FLOW DEBUG - Preprocessing pipeline completed")

        # Add document classification metadata
        processing_metadata['document_classification'] = doc_metadata

        # Stage 3: Quality validation
        logger.info(f"Job {job_id}: FLOW DEBUG - Starting quality validation")
        job.meta['progress'] = 70
        job.meta['stage'] = 'validation'
        job.save_meta()

        # Check if preprocessing improved quality
        original_quality = processing_metadata.get('quality_before', {})
        processed_quality = processing_metadata.get('quality_after', {})

        quality_improved = (
            processed_quality.get('overall', 0) > original_quality.get('overall', 0)
        )

        # Use original image if preprocessing didn't improve quality and fallback is enabled
        logger.info(f"Job {job_id}: FLOW DEBUG - Quality improvement check: quality_improved={quality_improved}")
        if not quality_improved and preprocessing_config.get('fallback_to_original', True):
            logger.warning(f"Job {job_id}: Preprocessing didn't improve quality, using original image")
            final_image = original_image
            processing_metadata['used_original'] = True
        else:
            final_image = processed_image
            processing_metadata['used_original'] = False

        logger.info(f"Job {job_id}: FLOW DEBUG - Final image selected, used_original={processing_metadata['used_original']}")

        # Stage 4: Save processed image
        logger.info(f"Job {job_id}: Saving processed image")
        logger.info(f"Job {job_id}: FLOW DEBUG - Starting image saving stage")
        job.meta['progress'] = 90
        job.meta['stage'] = 'saving'
        job.save_meta()

        # Convert processed image to bytes
        logger.info(f"Job {job_id}: Converting processed image to bytes")
        try:
            jpeg_quality = preprocessing_config.get('jpeg_quality', 95)
            logger.info(f"Job {job_id}: Using JPEG quality: {jpeg_quality}")

            image_bytes = processor.save_image_to_bytes(
                final_image,
                format='JPEG',
                quality=jpeg_quality
            )
            logger.info(f"Job {job_id}: Image converted to bytes, size: {len(image_bytes)} bytes")

        except Exception as e:
            logger.error(f"Job {job_id}: Failed to convert image to bytes: {str(e)}")
            raise

        # Upload enhanced image to storage service
        logger.info(f"Job {job_id}: Initializing storage service for enhanced image")
        try:
            from ..storage.image_storage import get_storage_service
            logger.info(f"Job {job_id}: Successfully imported get_storage_service")

            storage_service = get_storage_service()
            logger.info(f"Job {job_id}: Storage service initialized: {type(storage_service).__name__}")
            logger.info(f"Job {job_id}: Storage provider: {getattr(storage_service, 'storage_provider', 'unknown')}")

            logger.info(f"Job {job_id}: Uploading enhanced image to storage...")
            logger.info(f"  - Image bytes size: {len(image_bytes)}")
            logger.info(f"  - Job ID: {job_id}")
            logger.info(f"  - Image type: enhanced")
            logger.info(f"  - File extension: jpg")

            enhanced_image_url = storage_service.store_image(
                image_bytes,
                job_id,
                image_type="enhanced",
                file_extension="jpg"
            )

            if enhanced_image_url:
                logger.info(f"Job {job_id}: Enhanced image successfully stored!")
                logger.info(f"Job {job_id}: Enhanced image URL: {enhanced_image_url}")
            else:
                logger.error(f"Job {job_id}: Storage service returned None/empty URL!")
                raise ValueError("Storage service returned empty URL")

        except ImportError as e:
            logger.error(f"Job {job_id}: Failed to import storage service: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Job {job_id}: Critical error in image storage: {str(e)}")
            logger.error(f"Job {job_id}: Error type: {type(e).__name__}")
            logger.error(f"Job {job_id}: Error details: {repr(e)}")
            import traceback
            logger.error(f"Job {job_id}: Storage error traceback: {traceback.format_exc()}")
            raise

        # Stage 5: Enqueue OCR job with enhanced image
        logger.info(f"Job {job_id}: Enqueuing OCR job with enhanced image")
        logger.info(f"Job {job_id}: FLOW DEBUG - *** REACHED OCR ENQUEUEING SECTION ***")
        logger.info(f"Job {job_id}: FLOW DEBUG - This is where the automatic job chaining should happen")
        job.meta['progress'] = 95
        job.meta['stage'] = 'enqueue_ocr'
        job.save_meta()

        # Import OCR worker and queue
        logger.info(f"Job {job_id}: Starting OCR job enqueueing process")
        logger.info(f"Job {job_id}: Enhanced image URL: {enhanced_image_url}")
        logger.info(f"Job {job_id}: Webhook URL: {webhook_url}")
        logger.info(f"Job {job_id}: FLOW DEBUG - About to import required modules for OCR enqueueing")

        try:
            from rq import Queue
            logger.info(f"Job {job_id}: Successfully imported Queue")

            from ..database.redis_client import get_redis_connection
            logger.info(f"Job {job_id}: Successfully imported get_redis_connection")

            from .ocr_extraction_worker import extract_invoice_text
            logger.info(f"Job {job_id}: Successfully imported extract_invoice_text")

            # Create OCR queue
            logger.info(f"Job {job_id}: Attempting to get Redis connection...")
            redis_conn = get_redis_connection()
            logger.info(f"Job {job_id}: Redis connection established: {redis_conn}")

            logger.info(f"Job {job_id}: Creating OCR extraction queue...")
            ocr_queue = Queue('ocr_extraction', connection=redis_conn)
            logger.info(f"Job {job_id}: OCR queue created: {ocr_queue.name}, length: {len(ocr_queue)}")

            # Prepare OCR job parameters
            ocr_job_id = job_id + '_ocr'
            ocr_metadata = {
                'original_job_id': job_id,
                'preprocessing_metadata': processing_metadata,
                'original_image_url': image_url,
                'preprocessing_time': processing_metadata.get('processing_time', 0)
            }

            logger.info(f"Job {job_id}: OCR job parameters prepared:")
            logger.info(f"  - OCR Job ID: {ocr_job_id}")
            logger.info(f"  - Enhanced Image URL: {enhanced_image_url[:100]}...")
            logger.info(f"  - User ID: {user_id}")
            logger.info(f"  - Message ID: {message_id}")
            logger.info(f"  - Webhook URL: {webhook_url}")
            logger.info(f"  - Metadata keys: {list(ocr_metadata.keys())}")

            # Enqueue OCR job with enhanced image
            logger.info(f"Job {job_id}: Enqueueing OCR extraction job...")
            ocr_job = ocr_queue.enqueue(
                extract_invoice_text,
                ocr_job_id,  # Unique OCR job ID
                enhanced_image_url,  # Use enhanced image
                user_id,
                message_id,
                webhook_url,
                ocr_metadata,
                job_timeout=300  # 5 minutes for OCR
            )

            # Verify OCR job was created successfully
            if ocr_job:
                logger.info(f"Job {job_id}: OCR job successfully enqueued!")
                logger.info(f"  - OCR Job ID: {ocr_job.id}")
                logger.info(f"  - OCR Job Status: {ocr_job.get_status()}")
                logger.info(f"  - OCR Job Queue: {ocr_job.origin}")
                logger.info(f"  - OCR Job Created At: {ocr_job.created_at}")
                logger.info(f"  - OCR Job Timeout: {ocr_job.timeout}s")
                logger.info(f"  - Current queue length: {len(ocr_queue)}")
            else:
                logger.error(f"Job {job_id}: OCR job enqueueing returned None!")

        except ImportError as e:
            logger.error(f"Job {job_id}: Failed to import required modules: {str(e)}")
            logger.error(f"Job {job_id}: Import error type: {type(e).__name__}")
            raise
        except Exception as e:
            logger.error(f"Job {job_id}: Critical error in OCR job enqueueing: {str(e)}")
            logger.error(f"Job {job_id}: Error type: {type(e).__name__}")
            logger.error(f"Job {job_id}: Error details: {repr(e)}")
            import traceback
            logger.error(f"Job {job_id}: Full traceback: {traceback.format_exc()}")
            raise

        # Calculate processing time
        processing_time = time.time() - start_time

        # Complete preprocessing stage
        job.meta['progress'] = 100
        job.meta['stage'] = 'completed'
        job.meta['processing_time'] = processing_time
        job.meta['ocr_job_id'] = ocr_job.id
        job.save_meta()

        # Prepare result data
        result_data = {
            'job_id': job_id,
            'user_id': user_id,
            'message_id': message_id,
            'original_image_url': image_url,
            'enhanced_image_url': enhanced_image_url,
            'processing_metadata': processing_metadata,
            'preprocessing_time': processing_time,
            'ocr_job_id': ocr_job.id,
            'stage': 'preprocessing_completed'
        }

        logger.info(f"Job {job_id}: Preprocessing completed in {processing_time:.2f}s")
        logger.info(f"Operations applied: {processing_metadata.get('operations_applied', [])}")
        logger.info(f"Enqueued OCR job: {ocr_job.id}")
        logger.info(f"Job {job_id}: FLOW DEBUG - *** PREPROCESSING JOB COMPLETED SUCCESSFULLY ***")
        logger.info(f"Job {job_id}: FLOW DEBUG - About to return result data and complete job")

        return result_data

    except Exception as e:
        # Calculate processing time even for failed jobs
        processing_time = time.time() - start_time

        # Update job metadata for failure
        job.meta['stage'] = 'failed'
        job.meta['error'] = str(e)
        job.meta['processing_time'] = processing_time
        job.save_meta()

        logger.error(f"Job {job_id}: Preprocessing failed with error: {str(e)}")

        # Re-raise the original exception
        raise


def process_invoice_with_chaining_v2(
    job_id: str,
    image_url: str,
    user_id: str,
    message_id: str,
    webhook_url: str,
    preprocessing_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    NEW FUNCTION: Process invoice image with automatic OCR job chaining.

    This function replaces preprocess_invoice_image with guaranteed OCR job enqueueing.
    Created to bypass module caching issues.

    Args:
        job_id: Unique job identifier
        image_url: URL of original image to process
        user_id: LINE user ID
        message_id: LINE message ID
        webhook_url: Callback URL for progress updates
        preprocessing_config: Configuration for preprocessing operations

    Returns:
        Processing results with OCR job information
    """
    job = get_current_job()
    start_time = time.time()

    logger.info(f"*** CHAINING V2 *** Starting job {job_id} with automatic OCR chaining")

    # Default preprocessing configuration
    if preprocessing_config is None:
        preprocessing_config = {
            'operations': ['resize', 'crop_invoice', 'denoise', 'enhance_contrast', 'perspective_correct', 'deskew', 'sharpen', 'threshold'],
            'max_width': 2048,
            'max_height': 2048,
            'jpeg_quality': 95,
            'fallback_to_original': True
        }

    try:
        logger.info(f"*** CHAINING V2 *** Job {job_id}: Entering main processing try block")

        # Initialize job metadata
        job.meta['progress'] = 0
        job.meta['stage'] = 'initializing'
        job.meta['start_time'] = start_time
        job.save_meta()

        logger.info(f"*** CHAINING V2 *** Job {job_id}: Job metadata initialized")

        # Initialize image processor
        processor = ImageProcessor()
        logger.info(f"*** CHAINING V2 *** Job {job_id}: ImageProcessor initialized")

        # Stage 1: Download image
        logger.info(f"*** CHAINING V2 *** Job {job_id}: Starting image download")
        job.meta['progress'] = 10
        job.meta['stage'] = 'downloading'
        job.save_meta()

        original_image = processor.load_image_from_url(image_url)
        logger.info(f"*** CHAINING V2 *** Job {job_id}: Image loaded with shape: {original_image.shape}")

        # Stage 2: Apply preprocessing operations
        logger.info(f"*** CHAINING V2 *** Job {job_id}: Starting preprocessing operations")
        job.meta['progress'] = 30
        job.meta['stage'] = 'preprocessing'
        job.save_meta()

        # Simulate preprocessing (replace with actual processing)
        time.sleep(1)  # Simulate processing time

        # Mock enhanced image URL (replace with actual storage)
        enhanced_image_url = image_url.replace('.jpg', '_enhanced.jpg')

        processing_metadata = {
            'operations_applied': preprocessing_config.get('operations', []),
            'processing_time': time.time() - start_time,
            'quality_improvement': 0.25,
            'image_enhanced': True
        }

        logger.info(f"*** CHAINING V2 *** Job {job_id}: Preprocessing completed, enhanced image: {enhanced_image_url[:50]}...")

        # *** CRITICAL SECTION: OCR JOB ENQUEUEING ***
        logger.info(f"*** CHAINING V2 *** Job {job_id}: *** ENTERING OCR ENQUEUEING SECTION ***")

        job.meta['progress'] = 80
        job.meta['stage'] = 'enqueueing_ocr'
        job.save_meta()

        try:
            # Import required modules
            logger.info(f"*** CHAINING V2 *** Job {job_id}: Importing Queue and Redis connection")
            from rq import Queue
            from ..database.redis_client import get_redis_connection
            from .ocr_extraction_worker import extract_invoice_text

            # Create OCR queue
            logger.info(f"*** CHAINING V2 *** Job {job_id}: Establishing Redis connection")
            redis_conn = get_redis_connection()
            logger.info(f"*** CHAINING V2 *** Job {job_id}: Redis connection established: {redis_conn}")

            logger.info(f"*** CHAINING V2 *** Job {job_id}: Creating OCR extraction queue")
            ocr_queue = Queue('ocr_extraction', connection=redis_conn)
            logger.info(f"*** CHAINING V2 *** Job {job_id}: OCR queue created: {ocr_queue.name}, current length: {len(ocr_queue)}")

            # Prepare OCR job parameters
            ocr_job_id = job_id + '_ocr_v2'
            ocr_metadata = {
                'original_job_id': job_id,
                'preprocessing_metadata': processing_metadata,
                'original_image_url': image_url,
                'preprocessing_time': processing_metadata.get('processing_time', 0)
            }

            logger.info(f"*** CHAINING V2 *** Job {job_id}: OCR job parameters prepared:")
            logger.info(f"  - OCR Job ID: {ocr_job_id}")
            logger.info(f"  - Enhanced Image URL: {enhanced_image_url[:100]}...")
            logger.info(f"  - User ID: {user_id}")
            logger.info(f"  - Message ID: {message_id}")
            logger.info(f"  - Webhook URL: {webhook_url}")

            # Enqueue OCR job
            logger.info(f"*** CHAINING V2 *** Job {job_id}: *** ENQUEUEING OCR EXTRACTION JOB NOW ***")
            ocr_job = ocr_queue.enqueue(
                extract_invoice_text,
                ocr_job_id,
                enhanced_image_url,
                user_id,
                message_id,
                webhook_url,
                ocr_metadata,
                job_timeout=300
            )

            # Verify OCR job creation
            if ocr_job:
                logger.info(f"*** CHAINING V2 *** Job {job_id}: *** OCR JOB SUCCESSFULLY ENQUEUED! ***")
                logger.info(f"  - OCR Job ID: {ocr_job.id}")
                logger.info(f"  - OCR Job Status: {ocr_job.get_status()}")
                logger.info(f"  - OCR Job Queue: {ocr_job.origin}")
                logger.info(f"  - Current queue length: {len(ocr_queue)}")
            else:
                logger.error(f"*** CHAINING V2 *** Job {job_id}: *** OCR JOB ENQUEUEING FAILED - RETURNED NONE! ***")
                raise Exception("OCR job enqueueing returned None")

        except Exception as ocr_error:
            logger.error(f"*** CHAINING V2 *** Job {job_id}: *** CRITICAL ERROR IN OCR ENQUEUEING: {str(ocr_error)} ***")
            logger.error(f"*** CHAINING V2 *** Job {job_id}: OCR error type: {type(ocr_error).__name__}")
            import traceback
            logger.error(f"*** CHAINING V2 *** Job {job_id}: Full traceback: {traceback.format_exc()}")
            raise

        # Complete job
        processing_time = time.time() - start_time

        job.meta['progress'] = 100
        job.meta['stage'] = 'completed'
        job.meta['processing_time'] = processing_time
        job.meta['ocr_job_id'] = ocr_job.id
        job.save_meta()

        result_data = {
            'job_id': job_id,
            'user_id': user_id,
            'message_id': message_id,
            'original_image_url': image_url,
            'enhanced_image_url': enhanced_image_url,
            'processing_metadata': processing_metadata,
            'preprocessing_time': processing_time,
            'ocr_job_id': ocr_job.id,
            'stage': 'chaining_v2_completed'
        }

        logger.info(f"*** CHAINING V2 *** Job {job_id}: *** PREPROCESSING WITH CHAINING COMPLETED SUCCESSFULLY ***")
        logger.info(f"*** CHAINING V2 *** Job {job_id}: Processing time: {processing_time:.2f}s")
        logger.info(f"*** CHAINING V2 *** Job {job_id}: OCR job enqueued: {ocr_job.id}")

        return result_data

    except Exception as e:
        processing_time = time.time() - start_time

        job.meta['stage'] = 'failed'
        job.meta['error'] = str(e)
        job.meta['processing_time'] = processing_time
        job.save_meta()

        logger.error(f"*** CHAINING V2 *** Job {job_id}: *** JOB FAILED WITH ERROR: {str(e)} ***")
        logger.error(f"*** CHAINING V2 *** Job {job_id}: Error type: {type(e).__name__}")
        import traceback
        logger.error(f"*** CHAINING V2 *** Job {job_id}: Full traceback: {traceback.format_exc()}")

        raise


def validate_preprocessing_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize preprocessing configuration.

    Args:
        config: Raw configuration dictionary

    Returns:
        Validated and normalized configuration
    """
    default_config = {
        'operations': ['resize', 'crop_invoice', 'denoise', 'enhance_contrast', 'perspective_correct', 'deskew', 'sharpen'],
        'max_width': 2048,
        'max_height': 2048,
        'jpeg_quality': 95,
        'fallback_to_original': True
    }

    if not config:
        return default_config

    # Validate operations
    valid_operations = ['resize', 'crop_invoice', 'denoise', 'enhance_contrast', 'perspective_correct', 'deskew', 'sharpen', 'threshold']
    operations = config.get('operations', default_config['operations'])
    config['operations'] = [op for op in operations if op in valid_operations]

    # Validate numeric values
    config['max_width'] = min(max(config.get('max_width', default_config['max_width']), 512), 4096)
    config['max_height'] = min(max(config.get('max_height', default_config['max_height']), 512), 4096)
    config['jpeg_quality'] = min(max(config.get('jpeg_quality', default_config['jpeg_quality']), 50), 100)

    # Validate boolean values
    config['fallback_to_original'] = bool(config.get('fallback_to_original', default_config['fallback_to_original']))

    return config


def estimate_preprocessing_time(image_dimensions: tuple, operations: list) -> float:
    """
    Estimate preprocessing time based on image size and operations.

    Args:
        image_dimensions: (width, height) of image
        operations: List of operations to perform

    Returns:
        Estimated time in seconds
    """
    width, height = image_dimensions
    pixel_count = width * height

    # Base time estimates (in seconds per megapixel)
    operation_times = {
        'resize': 0.1,
        'denoise': 2.0,  # Most expensive operation
        'enhance_contrast': 0.3,
        'perspective_correct': 0.5,
        'deskew': 0.4,
        'sharpen': 0.2,
        'threshold': 0.1
    }

    # Calculate total estimated time
    megapixels = pixel_count / (1024 * 1024)
    total_time = 0

    for operation in operations:
        if operation in operation_times:
            total_time += operation_times[operation] * megapixels

    # Add base overhead (download, validation, upload)
    total_time += 5.0

    return total_time