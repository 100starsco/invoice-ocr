import os
from .types import QueueConfig

def get_queue_config() -> QueueConfig:
    return QueueConfig(
        default_queue=os.getenv('RQ_DEFAULT_QUEUE', 'default'),
        preprocessing_queue=os.getenv('RQ_PREPROCESSING_QUEUE', 'preprocessing'),
        ocr_queue=os.getenv('RQ_OCR_QUEUE', 'ocr'),
        retry_attempts=int(os.getenv('RQ_RETRY_ATTEMPTS', '3')),
        job_timeout=int(os.getenv('RQ_JOB_TIMEOUT', '300'))
    )