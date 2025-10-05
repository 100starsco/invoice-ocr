"""
Enhanced Logging Configuration for Development Testing

Provides structured logging with colored output, request tracing,
and detailed debug information for testing LINE chat integration.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for development."""

    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        # Add color to the level name
        level_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{level_color}{record.levelname}{self.RESET}"

        # Add color to logger name for better visibility
        if record.name.startswith('app.'):
            record.name = f"\033[34m{record.name}\033[0m"  # Blue for app modules

        return super().format(record)


class JobTrackingFilter(logging.Filter):
    """Filter that adds job context to log records."""

    def filter(self, record):
        # Try to extract job ID from message or add placeholder
        if hasattr(record, 'job_id'):
            record.job_context = f"[Job: {record.job_id}]"
        else:
            # Try to extract job ID from message
            msg = str(record.getMessage())
            if 'job' in msg.lower():
                import re
                job_match = re.search(r'job[_\s]([a-f0-9\-]+)', msg, re.IGNORECASE)
                if job_match:
                    record.job_context = f"[Job: {job_match.group(1)[:8]}...]"
                else:
                    record.job_context = "[Job: ?]"
            else:
                record.job_context = ""

        return True


def setup_development_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_colors: bool = True,
    enable_job_tracking: bool = True
) -> None:
    """
    Setup enhanced logging configuration for development testing.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        enable_colors: Enable colored console output
        enable_job_tracking: Enable job ID tracking in logs
    """
    # Clear existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Configure root logger
    logging.root.setLevel(getattr(logging, log_level.upper()))

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    if enable_colors and sys.stdout.isatty():
        console_format = ColoredFormatter(
            '%(asctime)s %(job_context)s %(name)s %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
    else:
        console_format = logging.Formatter(
            '%(asctime)s %(job_context)s %(name)s %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )

    console_handler.setFormatter(console_format)

    # Add job tracking filter if enabled
    if enable_job_tracking:
        console_handler.addFilter(JobTrackingFilter())

    logging.root.addHandler(console_handler)

    # File handler (no colors)
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setLevel(logging.DEBUG)  # Always debug level for file

        file_format = logging.Formatter(
            '%(asctime)s %(job_context)s [%(name)s] %(levelname)s - %(message)s '
            '[%(filename)s:%(lineno)d]',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)

        if enable_job_tracking:
            file_handler.addFilter(JobTrackingFilter())

        logging.root.addHandler(file_handler)

    # Set specific logger levels for better debugging
    loggers_config = {
        'app.workers.preprocessing_worker': logging.DEBUG,
        'app.workers.ocr_extraction_worker': logging.DEBUG,
        'app.core.image_processor': logging.DEBUG,
        'app.api.jobs': logging.DEBUG,
        'app.storage.image_storage': logging.DEBUG,
        'rq.worker': logging.INFO,
        'httpx': logging.WARNING,
        'uvicorn.access': logging.INFO,
        'uvicorn.error': logging.INFO,
    }

    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

    # Print startup message
    logger = logging.getLogger(__name__)
    logger.info("🚀 Enhanced development logging configured")
    logger.info(f"📊 Log level: {log_level}")
    logger.info(f"📝 Log file: {log_file or 'Console only'}")
    logger.info(f"🎨 Colors: {'Enabled' if enable_colors else 'Disabled'}")
    logger.info(f"🏷️ Job tracking: {'Enabled' if enable_job_tracking else 'Disabled'}")


def log_pipeline_stage(
    logger: logging.Logger,
    job_id: str,
    stage: str,
    progress: int,
    details: Optional[str] = None
) -> None:
    """
    Log processing pipeline stage with consistent formatting.

    Args:
        logger: Logger instance
        job_id: Job identifier
        stage: Processing stage name
        progress: Progress percentage (0-100)
        details: Optional additional details
    """
    progress_bar = "█" * (progress // 10) + "░" * (10 - progress // 10)
    message = f"[{progress_bar}] {progress:3d}% - {stage.upper()}"

    if details:
        message += f" - {details}"

    # Add job_id to log record for filtering
    logger.info(message, extra={'job_id': job_id})


def log_webhook_activity(
    logger: logging.Logger,
    event_type: str,
    webhook_url: str,
    job_id: str,
    success: bool,
    response_time: Optional[float] = None,
    error: Optional[str] = None
) -> None:
    """
    Log webhook activity with consistent formatting.

    Args:
        logger: Logger instance
        event_type: Type of webhook event
        webhook_url: Webhook URL (will be truncated for privacy)
        job_id: Associated job ID
        success: Whether webhook was successful
        response_time: Response time in seconds
        error: Error message if failed
    """
    # Truncate URL for privacy
    url_display = webhook_url[:30] + "..." if len(webhook_url) > 30 else webhook_url

    status = "✅ SUCCESS" if success else "❌ FAILED"
    message = f"📡 WEBHOOK {status} - {event_type} to {url_display}"

    if response_time is not None:
        message += f" ({response_time:.2f}s)"

    if error:
        message += f" - Error: {error}"

    level = logging.INFO if success else logging.ERROR
    logger.log(level, message, extra={'job_id': job_id})


def log_redis_activity(
    logger: logging.Logger,
    operation: str,
    key: Optional[str] = None,
    success: bool = True,
    details: Optional[str] = None
) -> None:
    """
    Log Redis operations with consistent formatting.

    Args:
        logger: Logger instance
        operation: Type of Redis operation
        key: Redis key (optional)
        success: Whether operation was successful
        details: Optional additional details
    """
    status = "✅" if success else "❌"
    message = f"{status} REDIS {operation.upper()}"

    if key:
        message += f" - {key}"

    if details:
        message += f" - {details}"

    level = logging.DEBUG if success else logging.WARNING
    logger.log(level, message)


# Convenience function for quick setup
def setup_dev_logging():
    """Quick setup for development logging with sensible defaults."""
    log_file = Path(__file__).parent.parent.parent / "dev-ocr-service.log"
    setup_development_logging(
        log_level="DEBUG",
        log_file=str(log_file),
        enable_colors=True,
        enable_job_tracking=True
    )