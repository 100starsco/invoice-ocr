"""
Language Detection Utility

Detects language of text regions to optimize OCR processing for Thai and English.
"""

import re
from typing import Dict, Tuple


def detect_text_language(text: str) -> Tuple[str, float]:
    """
    Detect the primary language of a text string.

    Args:
        text: Input text string

    Returns:
        Tuple of (language_code, confidence) where:
        - language_code: 'th' for Thai, 'en' for English, 'mixed' for both
        - confidence: 0.0 to 1.0 confidence score
    """
    if not text or len(text.strip()) == 0:
        return "unknown", 0.0

    # Character ranges
    thai_chars = len(re.findall(r'[ก-๙]', text))  # Thai Unicode range
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    digit_chars = len(re.findall(r'[0-9๐-๙]', text))  # Include Thai digits
    total_chars = len(re.sub(r'\s', '', text))  # Non-whitespace characters

    if total_chars == 0:
        return "unknown", 0.0

    # Calculate percentages
    thai_ratio = thai_chars / total_chars
    english_ratio = english_chars / total_chars
    digit_ratio = digit_chars / total_chars

    # Determine language based on character composition
    if thai_ratio > 0.3:
        if english_ratio > 0.2:
            # Mixed Thai and English
            confidence = min(thai_ratio + english_ratio, 0.95)
            return "mixed", confidence
        else:
            # Primarily Thai
            confidence = min(thai_ratio + 0.2, 0.95)
            return "th", confidence
    elif english_ratio > 0.5:
        # Primarily English
        confidence = min(english_ratio + 0.2, 0.95)
        return "en", confidence
    elif digit_ratio > 0.6:
        # Mostly numbers (common in invoices)
        return "numeric", 0.8
    else:
        # Unknown or insufficient data
        return "unknown", 0.3


def get_script_confidence(text: str) -> Dict[str, float]:
    """
    Get confidence scores for each script type in the text.

    Args:
        text: Input text string

    Returns:
        Dictionary with confidence scores for each script type
    """
    if not text or len(text.strip()) == 0:
        return {"thai": 0.0, "english": 0.0, "numeric": 0.0, "other": 0.0}

    # Count characters by type
    thai_chars = len(re.findall(r'[ก-๙]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    digit_chars = len(re.findall(r'[0-9๐-๙]', text))
    total_chars = len(re.sub(r'\s', '', text))

    if total_chars == 0:
        return {"thai": 0.0, "english": 0.0, "numeric": 0.0, "other": 0.0}

    other_chars = max(0, total_chars - thai_chars - english_chars - digit_chars)

    return {
        "thai": thai_chars / total_chars,
        "english": english_chars / total_chars,
        "numeric": digit_chars / total_chars,
        "other": other_chars / total_chars
    }


def is_thai_heavy_text(text: str, threshold: float = 0.2) -> bool:
    """
    Check if text contains significant Thai characters.

    Args:
        text: Input text string
        threshold: Minimum ratio of Thai characters (default: 0.2 = 20%)

    Returns:
        True if Thai character ratio exceeds threshold
    """
    script_conf = get_script_confidence(text)
    return script_conf["thai"] >= threshold


def should_use_thai_optimized_ocr(text: str) -> bool:
    """
    Determine if Thai-optimized OCR should be used for this text.

    Args:
        text: Input text string

    Returns:
        True if Thai-optimized OCR is recommended
    """
    language, confidence = detect_text_language(text)
    return language in ["th", "mixed"] and confidence > 0.5


def normalize_thai_text(text: str) -> str:
    """
    Normalize Thai text for better matching and comparison.

    Args:
        text: Input Thai text

    Returns:
        Normalized text
    """
    # Remove redundant spaces
    text = re.sub(r'\s+', ' ', text)

    # Normalize Thai vowels and tone marks (if needed)
    # This is a simplified version - full normalization requires more complex rules

    return text.strip()


def has_thai_invoice_keywords(text: str) -> bool:
    """
    Check if text contains common Thai invoice keywords.

    Args:
        text: Input text string

    Returns:
        True if Thai invoice keywords are found
    """
    thai_keywords = [
        'ใบเสร็จ',  # Receipt
        'ใบกำกับภาษี',  # Tax invoice
        'บริษัท',  # Company
        'ร้าน',  # Shop
        'ราคา',  # Price
        'รวม',  # Total
        'บาท',  # Baht
        'ยอดรวม',  # Sum/Total
        'เลขที่',  # Number
        'วันที่',  # Date
        'ภาษี',  # Tax
    ]

    text_lower = text.lower()
    return any(keyword in text_lower for keyword in thai_keywords)
