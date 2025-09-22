import os
from urllib.parse import urlparse
from .types import OCRServiceConfig

def validate_env_var(name: str, value: str, required: bool = True) -> str:
    """Validate environment variable exists and return its value."""
    if required and not value:
        raise ValueError(f"Environment variable {name} is required but not set")
    return value

def validate_url(name: str, value: str, required: bool = True) -> str:
    """Validate URL format."""
    url = validate_env_var(name, value, required)

    if url and required:
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise ValueError(f"Invalid URL format for {name}: {url}")
        except Exception:
            raise ValueError(f"Invalid URL for {name}: {url}")

    return url

def validate_positive_int(name: str, value: str, default: int) -> int:
    """Validate positive integer value."""
    if not value:
        return default

    try:
        int_value = int(value)
        if int_value <= 0:
            raise ValueError(f"{name} must be a positive integer, got: {value}")
        return int_value
    except ValueError:
        raise ValueError(f"Invalid integer value for {name}: {value}")

def validate_float_range(name: str, value: str, default: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Validate float value within range."""
    if not value:
        return default

    try:
        float_value = float(value)
        if not (min_val <= float_value <= max_val):
            raise ValueError(f"{name} must be between {min_val} and {max_val}, got: {value}")
        return float_value
    except ValueError:
        raise ValueError(f"Invalid float value for {name}: {value}")

def validate_config(config: OCRServiceConfig) -> None:
    """Validate the complete OCR service configuration."""

    # Validate MongoDB URI
    validate_url('MONGODB_URI', config.database.mongodb_uri)

    # Validate Redis URL
    validate_url('REDIS_URL', config.redis.url)

    # Validate RQ Dashboard Redis URL
    validate_url('RQ_DASHBOARD_REDIS_URL', config.monitoring.rq_dashboard_redis_url)

    # Validate OCR configuration
    if not config.ocr.language:
        raise ValueError("PADDLEOCR_LANG is required")

    if config.ocr.max_image_size <= 0:
        raise ValueError("PADDLEOCR_MAX_IMAGE_SIZE must be positive")

    if not (0.0 <= config.ocr.confidence_threshold <= 1.0):
        raise ValueError("PADDLEOCR_CONFIDENCE_THRESHOLD must be between 0.0 and 1.0")

    # Validate queue configuration
    if config.queue.retry_attempts < 0:
        raise ValueError("RQ_RETRY_ATTEMPTS must be non-negative")

    if config.queue.job_timeout <= 0:
        raise ValueError("RQ_JOB_TIMEOUT must be positive")

    # Validate monitoring configuration
    if not (1 <= config.monitoring.rq_dashboard_port <= 65535):
        raise ValueError("RQ_DASHBOARD_PORT must be between 1 and 65535")

    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if config.monitoring.log_level not in valid_log_levels:
        raise ValueError(f"LOG_LEVEL must be one of {valid_log_levels}")