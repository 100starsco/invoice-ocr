import os
from .types import OCRConfig

def get_ocr_config() -> OCRConfig:
    # Get language configuration, default to bilingual Thai+English
    lang_config = os.getenv('PADDLEOCR_LANG', 'th+en').lower()

    # Validate language configuration
    valid_languages = ['th', 'en', 'th+en']
    if lang_config not in valid_languages:
        print(f"Warning: Invalid PADDLEOCR_LANG '{lang_config}', using default 'th+en' (Thai+English)")
        lang_config = 'th+en'

    return OCRConfig(
        language=lang_config,
        use_gpu=os.getenv('PADDLEOCR_USE_GPU', 'false').lower() == 'true',
        max_image_size=int(os.getenv('PADDLEOCR_MAX_IMAGE_SIZE', '2048')),
        confidence_threshold=float(os.getenv('PADDLEOCR_CONFIDENCE_THRESHOLD', '0.3')),
        debug_mode=os.getenv('PADDLEOCR_DEBUG_MODE', 'false').lower() == 'true',
        use_angle_cls=os.getenv('PADDLEOCR_USE_ANGLE_CLS', 'true').lower() == 'true',
        use_space_char=os.getenv('PADDLEOCR_USE_SPACE_CHAR', 'true').lower() == 'true',
        dual_pass=os.getenv('PADDLEOCR_DUAL_PASS', 'true').lower() == 'true',
        det_db_thresh=float(os.getenv('PADDLEOCR_DET_DB_THRESH', '0.2')),
        drop_score=float(os.getenv('PADDLEOCR_DROP_SCORE', '0.3'))
    )