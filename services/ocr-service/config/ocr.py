import os
from .types import OCRConfig

def get_ocr_config() -> OCRConfig:
    return OCRConfig(
        language=os.getenv('PADDLEOCR_LANG', 'th'),
        use_gpu=os.getenv('PADDLEOCR_USE_GPU', 'false').lower() == 'true',
        max_image_size=int(os.getenv('PADDLEOCR_MAX_IMAGE_SIZE', '2048')),
        confidence_threshold=float(os.getenv('PADDLEOCR_CONFIDENCE_THRESHOLD', '0.8'))
    )