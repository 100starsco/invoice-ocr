from .environment import get_environment_config
from .database import get_database_config
from .redis import get_redis_config
from .ocr import get_ocr_config
from .queue import get_queue_config
from .monitoring import get_monitoring_config
from .validator import validate_config
from .types import OCRServiceConfig

def get_config() -> OCRServiceConfig:
    """Get the complete OCR service configuration."""
    config = OCRServiceConfig(
        environment=get_environment_config(),
        database=get_database_config(),
        redis=get_redis_config(),
        ocr=get_ocr_config(),
        queue=get_queue_config(),
        monitoring=get_monitoring_config()
    )

    # Validate configuration
    try:
        validate_config(config)
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        raise SystemExit(1)

    return config

# Create global config instance
config = get_config()

__all__ = [
    'config',
    'get_config',
    'validate_config',
    'OCRServiceConfig'
]