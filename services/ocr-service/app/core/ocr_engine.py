"""
OCR Engine

Main OCR processing engine using PaddleOCR for Thai text extraction.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from PIL import Image
import cv2

logger = logging.getLogger(__name__)


class OCREngine:
    """
    OCR Engine for processing Thai invoices using PaddleOCR.

    Handles text extraction, confidence scoring, and result formatting.
    """

    def __init__(self, language: str = "en", use_gpu: bool = False, dual_pass: bool = True):
        """
        Initialize OCR engine.

        Args:
            language: Language code for OCR. Supports:
                     - "th" for Thai only
                     - "en" for English only
                     - "th+en" for Thai+English (default, best for mixed documents)
            use_gpu: Whether to use GPU acceleration
            dual_pass: Enable dual-pass OCR for better bilingual recognition
        """
        self.language = language
        self.use_gpu = use_gpu
        self.dual_pass = dual_pass
        self._ocr_instance = None
        self._ocr_instance_secondary = None  # For dual-pass processing
        self._is_initialized = False
        self._supported_languages = ["th", "en", "th+en"]

    def initialize(self) -> None:
        """
        Initialize PaddleOCR instance.

        This should be called once before processing images.
        """
        try:
            # Import PaddleOCR
            from paddleocr import PaddleOCR

            # Validate and setup language configuration
            if self.language not in self._supported_languages:
                logger.warning(f"Unsupported language: {self.language}, defaulting to Thai+English (th+en)")
                self.language = "th+en"

            logger.info(f"Initializing PaddleOCR with language: {self.language}, GPU: {self.use_gpu}")

            # Language mapping for PaddleOCR
            language_desc = {
                "th": "Thai only",
                "en": "English only",
                "th+en": "Thai + English (bilingual)"
            }
            logger.info(f"OCR Language mode: {language_desc.get(self.language, self.language)}")

            # Initialize PaddleOCR with enhanced bilingual support
            # Strategy: Use 'ch' (Chinese) model for better Asian script recognition
            # including Thai characters, then optionally use 'en' for verification

            if self.language == "th+en":
                # Primary model: Chinese model has better Asian script support including Thai
                ocr_lang_primary = "ch"
                logger.info("Using Chinese model (primary) for enhanced Thai+English bilingual support")
                logger.info("Chinese model provides better recognition for Thai script characters")

                # Initialize primary OCR instance with optimized parameters
                self._ocr_instance = PaddleOCR(
                    use_angle_cls=True,  # Detect and correct text orientation
                    lang=ocr_lang_primary,
                    use_space_char=True,  # Preserve spaces between words
                    det_db_thresh=0.2,    # Lower threshold for better detection (was 0.3)
                    det_db_box_thresh=0.5,  # Box threshold for text regions
                    drop_score=0.3,       # Drop low-confidence results
                    use_gpu=self.use_gpu
                )

                # Initialize secondary OCR instance for dual-pass if enabled
                if self.dual_pass:
                    logger.info("Initializing secondary English model for dual-pass verification")
                    self._ocr_instance_secondary = PaddleOCR(
                        use_angle_cls=True,
                        lang="en",
                        use_space_char=True,
                        det_db_thresh=0.2,
                        drop_score=0.3,
                        use_gpu=self.use_gpu
                    )
                    logger.info("Dual-pass OCR mode enabled (Chinese + English models)")
                else:
                    logger.info("Single-pass OCR mode (Chinese model only)")

            elif self.language == "th":
                # Thai-only mode: still use Chinese model for better Thai support
                ocr_lang = "ch"
                logger.info("Using Chinese model for Thai-only mode (better Thai script support)")
                self._ocr_instance = PaddleOCR(
                    use_angle_cls=True,
                    lang=ocr_lang,
                    use_space_char=True,
                    det_db_thresh=0.2,
                    drop_score=0.3,
                    use_gpu=self.use_gpu
                )
            else:
                # English or other languages
                ocr_lang = self.language
                logger.info(f"Using {ocr_lang} model for single-language mode")
                self._ocr_instance = PaddleOCR(
                    use_angle_cls=True,
                    lang=ocr_lang,
                    use_space_char=True,
                    det_db_thresh=0.2,
                    drop_score=0.3,
                    use_gpu=self.use_gpu
                )

            self._is_initialized = True
            logger.info("PaddleOCR engine initialized successfully")
            logger.info(f"Configuration: language={self.language}, dual_pass={self.dual_pass}, gpu={self.use_gpu}")

        except ImportError as e:
            logger.error(f"Failed to import PaddleOCR: {e}")
            logger.error("Please install PaddleOCR: pip install paddleocr")
            raise RuntimeError("PaddleOCR not available")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise RuntimeError(f"OCR engine initialization failed: {e}")

    def extract_text(
        self,
        image: np.ndarray,
        confidence_threshold: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        Extract text from image with confidence scores using dual-pass OCR if enabled.

        Args:
            image: Input image as numpy array
            confidence_threshold: Minimum confidence score for text detection

        Returns:
            List of text extraction results with bounding boxes and confidence
        """
        if not self.is_initialized():
            raise RuntimeError("OCR engine not initialized. Call initialize() first.")

        try:
            logger.info(f"Starting PaddleOCR text extraction with confidence threshold: {confidence_threshold}")

            # Primary OCR pass (Chinese model for Thai+English)
            logger.info("Running primary OCR pass (Chinese model for Asian scripts)...")
            result_primary = self._ocr_instance.ocr(image, cls=True)

            # Log raw OCR result structure for debugging
            logger.debug(f"Primary OCR result structure: {type(result_primary)}, length: {len(result_primary) if result_primary else 0}")

            # Process primary OCR results
            text_regions = self._process_ocr_results(
                result_primary,
                confidence_threshold,
                ocr_pass="primary"
            )

            # Dual-pass OCR: Run secondary pass with English model if enabled
            if self.dual_pass and self._ocr_instance_secondary and self.language == "th+en":
                logger.info("Running secondary OCR pass (English model for verification)...")
                result_secondary = self._ocr_instance_secondary.ocr(image, cls=True)

                logger.debug(f"Secondary OCR result structure: {type(result_secondary)}, length: {len(result_secondary) if result_secondary else 0}")

                # Process secondary results
                text_regions_secondary = self._process_ocr_results(
                    result_secondary,
                    confidence_threshold,
                    ocr_pass="secondary"
                )

                # Merge results from both passes
                text_regions = self._merge_dual_pass_results(
                    text_regions,
                    text_regions_secondary
                )

                logger.info(f"Dual-pass OCR completed: {len(text_regions)} text regions after merge")

            # Filter regions that meet confidence threshold for primary processing
            primary_regions = [r for r in text_regions if r["above_threshold"]]
            all_regions_count = len(text_regions)
            primary_count = len(primary_regions)

            logger.info(f"PaddleOCR Results Summary:")
            logger.info(f"  Total text regions found: {all_regions_count}")
            logger.info(f"  Regions above threshold ({confidence_threshold}): {primary_count}")
            logger.info(f"  Low confidence regions: {all_regions_count - primary_count}")

            if all_regions_count == 0:
                logger.warning("⚠ PaddleOCR found NO text regions in image!")
            elif primary_count == 0:
                logger.warning(f"⚠ No text regions meet confidence threshold {confidence_threshold}. Consider lowering threshold.")
                # Log the highest confidence found
                if text_regions:
                    max_conf = max(r["confidence"] for r in text_regions)
                    logger.warning(f"  Highest confidence found: {max_conf:.3f}")

            return text_regions

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            raise RuntimeError(f"OCR text extraction failed: {e}")

    def _process_ocr_results(
        self,
        result: Any,
        confidence_threshold: float,
        ocr_pass: str = "primary"
    ) -> List[Dict[str, Any]]:
        """
        Process OCR results into structured format with language detection.

        Args:
            result: Raw OCR result from PaddleOCR
            confidence_threshold: Minimum confidence threshold
            ocr_pass: Name of OCR pass ("primary" or "secondary")

        Returns:
            List of processed text regions
        """
        from ..utils.language_detector import detect_text_language, get_script_confidence

        text_regions = []

        if result and len(result) > 0:
            for line in result[0] if result[0] else []:
                if line and len(line) >= 2:
                    # Extract bounding box and text info
                    bbox = line[0]  # Bounding box coordinates
                    text_info = line[1]  # (text, confidence)

                    if text_info and len(text_info) >= 2:
                        text = text_info[0]
                        confidence = float(text_info[1])

                        # Detect language of text region
                        language, lang_confidence = detect_text_language(text)
                        script_conf = get_script_confidence(text)

                        # Convert bbox to integer coordinates
                        bbox_int = [[int(x), int(y)] for x, y in bbox]

                        # Create region data with language information
                        region_data = {
                            "text": text,
                            "confidence": confidence,
                            "bounding_box": bbox_int,
                            "bbox_polygon": bbox,
                            "above_threshold": confidence >= confidence_threshold,
                            "language": language,
                            "language_confidence": lang_confidence,
                            "script_confidence": script_conf,
                            "ocr_pass": ocr_pass
                        }

                        text_regions.append(region_data)

                        # Log text with language information
                        status = "✓" if confidence >= confidence_threshold else "✗"
                        lang_tag = f"[{language.upper()}]" if language != "unknown" else ""
                        logger.info(f"{status} {lang_tag} Text: '{text[:50]}{'...' if len(text) > 50 else ''}' (conf: {confidence:.3f}, lang_conf: {lang_confidence:.2f})")

        return text_regions

    def _merge_dual_pass_results(
        self,
        primary_regions: List[Dict[str, Any]],
        secondary_regions: List[Dict[str, Any]],
        iou_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Merge results from dual-pass OCR, choosing best result for each text region.

        Args:
            primary_regions: Results from primary OCR pass
            secondary_regions: Results from secondary OCR pass
            iou_threshold: IoU threshold for matching overlapping regions

        Returns:
            Merged list of text regions with best results
        """
        from ..utils.language_detector import is_thai_heavy_text

        merged_regions = []
        used_secondary = set()

        # For each primary region, find matching secondary region and choose best
        for primary in primary_regions:
            best_match = primary
            best_match_idx = None

            # Find overlapping regions in secondary results
            for idx, secondary in enumerate(secondary_regions):
                if idx in used_secondary:
                    continue

                # Calculate IoU (Intersection over Union) for bounding boxes
                iou = self._calculate_bbox_iou(
                    primary["bounding_box"],
                    secondary["bounding_box"]
                )

                if iou >= iou_threshold:
                    # Regions overlap significantly
                    # Choose based on language and confidence
                    primary_text = primary["text"]
                    secondary_text = secondary["text"]

                    # If primary text is Thai-heavy, prefer primary result
                    if is_thai_heavy_text(primary_text):
                        if primary["confidence"] >= secondary["confidence"] * 0.8:
                            # Keep primary (Chinese model better for Thai)
                            best_match = primary
                        else:
                            # Secondary has much higher confidence
                            best_match = secondary
                            best_match_idx = idx
                    else:
                        # English text: prefer secondary (English model)
                        if secondary["confidence"] >= primary["confidence"] * 0.8:
                            best_match = secondary
                            best_match_idx = idx
                        else:
                            best_match = primary

                    if best_match_idx is not None:
                        used_secondary.add(best_match_idx)
                    break

            # Add indicator if result was improved by dual-pass
            if best_match == primary:
                best_match["dual_pass_improved"] = False
            else:
                best_match["dual_pass_improved"] = True
                logger.debug(f"Dual-pass improvement: '{primary['text'][:30]}' -> '{best_match['text'][:30]}'")

            merged_regions.append(best_match)

        # Add any unmatched secondary regions
        for idx, secondary in enumerate(secondary_regions):
            if idx not in used_secondary:
                secondary["dual_pass_improved"] = False
                merged_regions.append(secondary)

        logger.info(f"Merged {len(primary_regions)} primary + {len(secondary_regions)} secondary = {len(merged_regions)} total regions")
        improved_count = sum(1 for r in merged_regions if r.get("dual_pass_improved", False))
        logger.info(f"Dual-pass improved {improved_count} regions")

        return merged_regions

    def _calculate_bbox_iou(
        self,
        bbox1: List[List[int]],
        bbox2: List[List[int]]
    ) -> float:
        """
        Calculate Intersection over Union (IoU) for two bounding boxes.

        Args:
            bbox1: First bounding box as list of [x, y] coordinates
            bbox2: Second bounding box as list of [x, y] coordinates

        Returns:
            IoU score (0.0 to 1.0)
        """
        # Convert bbox to (x_min, y_min, x_max, y_max) format
        def bbox_to_rect(bbox):
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

        x1_min, y1_min, x1_max, y1_max = bbox_to_rect(bbox1)
        x2_min, y2_min, x2_max, y2_max = bbox_to_rect(bbox2)

        # Calculate intersection area
        x_inter_min = max(x1_min, x2_min)
        y_inter_min = max(y1_min, y2_min)
        x_inter_max = min(x1_max, x2_max)
        y_inter_max = min(y1_max, y2_max)

        if x_inter_max < x_inter_min or y_inter_max < y_inter_min:
            return 0.0

        inter_area = (x_inter_max - x_inter_min) * (y_inter_max - y_inter_min)

        # Calculate union area
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = area1 + area2 - inter_area

        if union_area == 0:
            return 0.0

        return inter_area / union_area

    def extract_invoice_fields(
        self,
        image: np.ndarray,
        fallback_low_confidence: bool = True
    ) -> Dict[str, Any]:
        """
        Extract structured invoice fields from image.

        Args:
            image: Input invoice image

        Returns:
            Dictionary containing extracted invoice fields
        """
        # First extract all text regions with primary confidence threshold
        if self.config.debug_mode:
            logger.info(f"Starting invoice field extraction with confidence threshold: {self.config.confidence_threshold}")

        text_regions = self.extract_text(image, confidence_threshold=self.config.confidence_threshold)

        if self.config.debug_mode:
            logger.info(f"Initial OCR extraction found {len(text_regions)} text regions")
            for i, region in enumerate(text_regions[:5]):  # Log first 5 regions
                logger.info(f"Region {i}: '{region['text'][:50]}' (confidence: {region['confidence']:.3f})")

        # If no high-confidence text found, try with lower threshold
        primary_regions = [r for r in text_regions if r.get("above_threshold", True)]
        if not primary_regions and fallback_low_confidence:
            if self.config.debug_mode:
                logger.warning(f"No high-confidence text found. Trying with lower threshold (0.1)...")
            else:
                logger.warning("No high-confidence text found. Trying with lower threshold (0.1)...")
            text_regions = self.extract_text(image, confidence_threshold=0.1)
            primary_regions = [r for r in text_regions if r["confidence"] >= 0.1]

            if self.config.debug_mode:
                logger.info(f"Fallback extraction found {len(text_regions)} additional regions")

        if not text_regions:
            return {
                "vendor": {"value": None, "confidence": 0.0},
                "invoice_number": {"value": None, "confidence": 0.0},
                "date": {"value": None, "confidence": 0.0},
                "total_amount": {"value": None, "confidence": 0.0},
                "line_items": []
            }

        # Use regions that are usable (either above threshold or in fallback mode)
        usable_regions = [r for r in text_regions if r.get("above_threshold", True) or r["confidence"] >= 0.1]

        # Extract full text for parsing
        full_text = " ".join([region["text"] for region in usable_regions])

        if self.config.debug_mode:
            logger.info(f"Field extraction working with {len(usable_regions)} usable text regions")
            logger.info(f"Full extracted text: '{full_text[:200]}{'...' if len(full_text) > 200 else ''}'")
            logger.info("Starting individual field extraction...")
        else:
            logger.info(f"Field extraction working with {len(usable_regions)} usable text regions")
            logger.info(f"Full extracted text: '{full_text[:200]}{'...' if len(full_text) > 200 else ''}'")

        # Parse structured fields using both Thai and international patterns
        if self.config.debug_mode:
            logger.info("Extracting vendor information...")
        vendor_result = self._extract_vendor(usable_regions, full_text)

        if self.config.debug_mode:
            logger.info("Extracting invoice number...")
        invoice_number_result = self._extract_invoice_number(usable_regions, full_text)

        if self.config.debug_mode:
            logger.info("Extracting date information...")
        date_result = self._extract_date(usable_regions, full_text)

        if self.config.debug_mode:
            logger.info("Extracting total amount...")
        total_amount_result = self._extract_total_amount(usable_regions, full_text)

        if self.config.debug_mode:
            logger.info("Extracting line items...")
        line_items_result = self._extract_line_items(usable_regions, full_text)

        invoice_fields = {
            "vendor": vendor_result,
            "invoice_number": invoice_number_result,
            "date": date_result,
            "total_amount": total_amount_result,
            "line_items": line_items_result
        }

        if self.config.debug_mode:
            logger.info("=== FINAL EXTRACTION RESULTS ===")
            logger.info(f"Vendor: {vendor_result['value']} (confidence: {vendor_result['confidence']:.3f})")
            logger.info(f"Invoice Number: {invoice_number_result['value']} (confidence: {invoice_number_result['confidence']:.3f})")
            logger.info(f"Date: {date_result['value']} (confidence: {date_result['confidence']:.3f})")
            logger.info(f"Total Amount: {total_amount_result['value']} (confidence: {total_amount_result['confidence']:.3f})")
            logger.info(f"Line Items: {len(line_items_result)} items found")
            overall_confidence = (vendor_result['confidence'] + invoice_number_result['confidence'] + date_result['confidence'] + total_amount_result['confidence']) / 4
            logger.info(f"Overall extraction confidence: {overall_confidence:.3f}")

        return invoice_fields

    def get_text_regions(
        self,
        image: np.ndarray
    ) -> List[Tuple[List[List[int]], str, float]]:
        """
        Get text regions with bounding boxes.

        Args:
            image: Input image

        Returns:
            List of (bounding_box, text, confidence) tuples
        """
        text_regions = self.extract_text(image)
        return [
            (region["bounding_box"], region["text"], region["confidence"])
            for region in text_regions
        ]

    def calculate_overall_confidence(
        self,
        results: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate overall confidence score for OCR results.

        Args:
            results: List of OCR extraction results

        Returns:
            Overall confidence score (0.0 to 1.0)
        """
        if not results:
            return 0.0

        # Calculate weighted average confidence
        total_confidence = 0.0
        total_weight = 0.0

        for result in results:
            confidence = result.get("confidence", 0.0)
            # Weight by text length (longer text typically more reliable)
            text_length = len(result.get("text", ""))
            weight = max(1.0, text_length / 10.0)  # Minimum weight of 1.0

            total_confidence += confidence * weight
            total_weight += weight

        return total_confidence / total_weight if total_weight > 0 else 0.0

    def is_initialized(self) -> bool:
        """
        Check if OCR engine is initialized.

        Returns:
            True if engine is ready for processing
        """
        return self._is_initialized and self._ocr_instance is not None

    def cleanup(self) -> None:
        """
        Clean up OCR engine resources.
        """
        if self._ocr_instance:
            # PaddleOCR doesn't have explicit cleanup, but we can clear the reference
            self._ocr_instance = None
        self._is_initialized = False
        logger.info("OCR engine cleaned up")

    # Private helper methods for field extraction

    def _extract_vendor(self, text_regions: List[Dict], full_text: str) -> Dict[str, Any]:
        """Extract vendor/shop name from text regions using enhanced Thai and international patterns."""
        # Enhanced Thai and international vendor patterns
        vendor_patterns = [
            # High-priority Thai patterns
            r'ร้าน\s*([ก-๙a-zA-Z0-9\s&]{2,50})',  # "ร้าน" (shop) with improved capture
            r'บริษัท\s*([ก-๙a-zA-Z0-9\s&]{2,60})',  # "บริษัท" (company) with mixed script
            r'ห้างหุ้นส่วน\s*([ก-๙a-zA-Z0-9\s]{2,60})',  # Partnership
            r'ห้าง\s*([ก-๙a-zA-Z0-9\s]{2,40})',  # "ห้าง" (department store/shop)
            r'ผู้ขาย[:\s]*([ก-๙a-zA-Z0-9\s]{2,50})',  # "ผู้ขาย" (seller)
            r'ชื่อผู้ประกอบการ[:\s]*([ก-๙a-zA-Z0-9\s]{2,50})',  # "ชื่อผู้ประกอบการ" (business name)

            # International patterns with better capture
            r'(?:company|corp|corporation|inc|ltd|limited|llc|llp)[.:\s]+([^\n]{2,50})',
            r'([A-Z][a-z\s&]{2,50}(?:Company|Corp|Inc|Ltd|Limited|LLC|LLP))',
            r'(?:bill\s+to|sold\s+by|from|vendor)[:\s]+([^\n]{2,50})',
            r'(?:merchant|seller|supplier)[:\s]+([^\n]{2,50})',

            # Mixed Thai-English patterns
            r'([ก-๙]{3,}[\s]*[A-Z][a-zA-Z\s]{2,40})',  # Thai followed by English
            r'([A-Z][a-zA-Z\s]{2,20}[\s]*[ก-๙]{3,})',  # English followed by Thai
        ]

        best_match = {"value": None, "confidence": 0.0}

        # Look for vendor patterns in individual text regions first
        for region in text_regions:
            text = region["text"]
            confidence = region["confidence"]

            for pattern in vendor_patterns:
                match = re.search(pattern, text)
                if match and confidence > best_match["confidence"]:
                    best_match = {
                        "value": match.group().strip(),
                        "confidence": confidence
                    }

        # If no pattern match, try positional heuristics and fallback strategies
        if not best_match["value"]:
            # Try the first few high-confidence regions (likely header/vendor info)
            candidate_regions = [r for r in text_regions if r["confidence"] > 0.7 and len(r["text"]) > 3]

            for i, region in enumerate(candidate_regions[:3]):  # Check top 3 regions
                text = region["text"].strip()

                # Skip obvious non-vendor patterns
                if not any([
                    text.lower() in ['receipt', 'invoice', 'bill', 'total', 'tax', 'vat'],
                    text.replace(' ', '').isdigit(),  # Skip pure numbers
                    len(text.split()) > 8,  # Skip very long text (likely descriptions)
                    any(char in text for char in ['@', 'http', 'www'])  # Skip emails/URLs
                ]):
                    confidence_multiplier = 0.8 if i == 0 else 0.6 - (i * 0.1)  # Higher confidence for first regions
                    best_match = {
                        "value": text,
                        "confidence": region["confidence"] * confidence_multiplier
                    }
                    logger.info(f"Vendor fallback: '{text}' (position: {i+1}, confidence: {region['confidence']:.3f})")
                    break

        # Final fallback: use any text if nothing found
        if not best_match["value"] and text_regions:
            # Look for the longest meaningful text first
            meaningful_regions = [r for r in text_regions if len(r["text"].strip()) > 2]
            if meaningful_regions:
                fallback_region = max(meaningful_regions, key=lambda r: len(r["text"]) * r["confidence"])
                confidence_multiplier = 0.4 if len(fallback_region["text"]) > 5 else 0.3
                best_match = {
                    "value": fallback_region["text"].strip(),
                    "confidence": fallback_region["confidence"] * confidence_multiplier
                }
                if self.config.debug_mode:
                    logger.info(f"Vendor desperate fallback: '{fallback_region['text']}' (confidence: {fallback_region['confidence']:.3f}, final: {best_match['confidence']:.3f})")

        return best_match

    def _extract_invoice_number(self, text_regions: List[Dict], full_text: str) -> Dict[str, Any]:
        """Extract invoice number from text regions."""
        # Thai invoice number patterns
        invoice_patterns = [
            r'(?:เลขที่|เลข|หมายเลข)[:\s]*([A-Z0-9\-\/]{3,20})',
            r'(?:INV|INVOICE)[:\s\-]*([A-Z0-9\-\/]{3,20})',
            r'(?:No\.?|NO)[:\s]*([A-Z0-9\-\/]{3,20})',
        ]

        best_match = {"value": None, "confidence": 0.0}

        for region in text_regions:
            text = region["text"]
            confidence = region["confidence"]

            for pattern in invoice_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match and confidence > best_match["confidence"]:
                    best_match = {
                        "value": match.group(1).strip(),
                        "confidence": confidence
                    }

        return best_match

    def _extract_date(self, text_regions: List[Dict], full_text: str) -> Dict[str, Any]:
        """Extract date from text regions with enhanced Thai patterns and Buddhist calendar support."""
        # Enhanced Thai and international date patterns with Buddhist calendar support
        date_patterns = [
            # High-priority Thai patterns with labels
            r'(?:วันที่|date|ลงวันที่)[:\s]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
            r'(?:วันที่|ว/ด/ป)[:\s]*(\d{1,2}\s+[ก-์]{2,15}\s+\d{4})',  # Thai month names with label
            r'(?:วันที่)[:\s]*(\d{1,2}[\s\-\/\.]+\d{1,2}[\s\-\/\.]+\d{2,4})',  # Thai date label variations

            # Thai month names (full and abbreviated)
            r'(\d{1,2}\s+(?:ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.)\s+\d{2,4})',  # Abbreviated
            r'(\d{1,2}\s+(?:มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s+(?:พ\.ศ\.\s*)?\d{2,4})',  # Full with optional Buddhist era
            r'(\d{1,2}\s+(?:ม\.?ค|ก\.?พ|มี\.?ค|เม\.?ย|พ\.?ค|มิ\.?ย|ก\.?ค|ส\.?ค|ก\.?ย|ต\.?ค|พ\.?ย|ธ\.?ค)[\.:\s]+\d{2,4})',  # Flexible abbreviation

            # Standard date formats (prioritized by year digits)
            r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4})',  # DD/MM/YYYY (Buddhist or Gregorian)
            r'(\d{1,2}\s*[\/\-\.]\s*\d{1,2}\s*[\/\-\.]\s*\d{4})',  # With spaces, 4-digit year
            r'(\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})',  # YYYY/MM/DD format
            r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2})',  # DD/MM/YY (fallback, 2-digit year)
            r'(\d{1,2}\s*[\/\-\.]\s*\d{1,2}\s*[\/\-\.]\s*\d{2})',  # With spaces, 2-digit year

            # International formats
            r'(\d{1,2}[\/\-\.]\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*[\/\-\.]\s*\d{2,4})',  # English months
        ]

        best_match = {"value": None, "confidence": 0.0}
        candidates = []

        for region in text_regions:
            text = region["text"]
            confidence = region["confidence"]

            for i, pattern in enumerate(date_patterns):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    date_value = match.group(1).strip()

                    # Calculate score based on pattern priority and confidence
                    pattern_score = 1.0 - (i * 0.1)  # Earlier patterns get higher scores
                    total_score = confidence * pattern_score

                    candidates.append({
                        "value": date_value,
                        "confidence": confidence,
                        "score": total_score,
                        "pattern_index": i,
                        "source_text": text
                    })

                    if self.config.debug_mode:
                        logger.info(f"Date candidate: '{date_value}' from '{text}' (pattern {i}, confidence: {confidence:.3f}, score: {total_score:.3f})")

        # Select best candidate based on score
        if candidates:
            best_candidate = max(candidates, key=lambda x: x["score"])

            # Apply confidence threshold filtering
            if best_candidate["confidence"] >= self.config.confidence_threshold:
                confidence_multiplier = 1.0
            else:
                confidence_multiplier = 0.8  # Reduce confidence for low-quality OCR

            best_match = {
                "value": best_candidate["value"],
                "confidence": best_candidate["confidence"] * confidence_multiplier
            }

            if self.config.debug_mode:
                logger.info(f"Selected date: '{best_candidate['value']}' (pattern {best_candidate['pattern_index']}, score: {best_candidate['score']:.3f}, final confidence: {best_match['confidence']:.3f})")
                logger.info(f"Total date candidates found: {len(candidates)}")

        return best_match

    def _extract_total_amount(self, text_regions: List[Dict], full_text: str) -> Dict[str, Any]:
        """Extract total amount from text regions using enhanced Thai and international patterns."""
        # Enhanced Thai and international amount patterns with better Thai digit support
        amount_patterns = [
            # High-priority Thai patterns with flexible spacing
            r'(?:รวมทั้งสิ้น|ยอดรวมทั้งสิ้น)[:\s]*([0-9,๐-๙]+\.?\d*)\s*(?:บาท)?',  # Most formal
            r'(?:ยอดสุทธิ|จำนวนเงินสุทธิ)[:\s]*([0-9,๐-๙]+\.?\d*)\s*(?:บาท)?',  # Net amount
            r'(?:ราคารวม|ราคาทั้งหมด)[:\s]*([0-9,๐-๙]+\.?\d*)\s*(?:บาท)?',  # Total price
            r'(?:รวม|ยอดรวม)[:\s]*([0-9,๐-๙]+\.?\d*)\s*(?:บาท)?',  # Total
            r'(?:ทั้งหมด|จำนวนเงิน)[:\s]*([0-9,๐-๙]+\.?\d*)\s*(?:บาท)?',  # Amount
            r'(?:เป็นเงิน)[:\s]*([0-9,๐-๙]+\.?\d*)\s*(?:บาท)?',  # "เป็นเงิน" (amount is)

            # Thai with currency symbol
            r'([0-9,๐-๙]+\.?\d{1,2})\s*(?:บาท|฿)',  # Amount with baht or symbol
            r'(?:บาท|฿)\s*([0-9,๐-๙]+\.?\d*)',  # Currency prefix
            r'([0-9,๐-๙]+\.?\d{1,2})\s*(?:THB|Baht)',  # International currency code

            # International patterns with better matching
            r'(?:total|sum|amount|grand\s+total|net\s+total)[:\s]*([0-9,]+\.?\d*)\s*(?:THB|บาท|฿)?',
            r'(?:total\s+amount|total\s+price)[:\s]*([0-9,]+\.?\d*)',
            r'(?:subtotal|sub\s*total)[:\s]*([0-9,]+\.?\d*)',
            r'(?:balance|balance\s+due)[:\s]*([0-9,]+\.?\d*)',

            # Amount with currency indicators
            r'([0-9,]+\.\d{1,2})\s*(?:THB|บาท|฿|USD|EUR|GBP)',
            r'(?:THB|฿)\s*([0-9,]+\.?\d*)',
            r'\$\s*([0-9,]+\.?\d*)',

            # Generic patterns for fallback (lower priority)
            r'([0-9,]{4,}\.\d{2})(?!\s*[0-9])',  # Large amounts with 2 decimals
            r'([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]{1,2})?)',  # Comma-separated thousands
        ]

        best_match = {"value": None, "confidence": 0.0}
        candidates = []  # Store all potential amounts with scores

        # First pass: look for pattern-based matches
        for region in text_regions:
            text = region["text"]
            confidence = region["confidence"]

            for i, pattern in enumerate(amount_patterns):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        # Parse amount and remove commas
                        amount_str = match.group(1).replace(",", "")
                        amount_value = float(amount_str)

                        # Skip obviously invalid amounts
                        if amount_value <= 0 or amount_value > 1000000:  # Skip negative or unreasonably large amounts
                            continue

                        # Calculate score based on pattern priority and confidence
                        pattern_score = 1.0 - (i * 0.05)  # Earlier patterns get higher scores
                        total_score = confidence * pattern_score

                        candidates.append({
                            "value": amount_value,
                            "confidence": confidence,
                            "score": total_score,
                            "pattern_index": i,
                            "source_text": text
                        })

                        if self.config.debug_mode:
                            logger.info(f"Amount candidate: {amount_value} from '{text}' (pattern {i}, confidence: {confidence:.3f}, score: {total_score:.3f})")

                    except (ValueError, IndexError):
                        continue

        # Select best candidate based on score
        if candidates:
            best_candidate = max(candidates, key=lambda x: x["score"])

            # Apply confidence threshold filtering
            if best_candidate["confidence"] >= self.config.confidence_threshold:
                confidence_multiplier = 1.0
            else:
                confidence_multiplier = 0.7  # Reduce confidence for low-quality OCR

            best_match = {
                "value": best_candidate["value"],
                "confidence": best_candidate["confidence"] * confidence_multiplier
            }

            if self.config.debug_mode:
                logger.info(f"Selected amount: {best_candidate['value']} (pattern {best_candidate['pattern_index']}, score: {best_candidate['score']:.3f}, final confidence: {best_match['confidence']:.3f})")
                logger.info(f"Total amount candidates found: {len(candidates)}")

        # Fallback: look for the largest reasonable number if no pattern matches
        if not best_match["value"]:
            logger.info("No pattern-based amount found, trying fallback heuristics...")

            number_candidates = []
            for region in text_regions:
                text = region["text"]
                confidence = region["confidence"]

                # Look for any number that could be an amount
                numbers = re.findall(r'([0-9,]+(?:\.[0-9]{1,2})?)', text)
                for num_str in numbers:
                    try:
                        amount_value = float(num_str.replace(",", ""))
                        if 1.0 <= amount_value <= 100000:  # Reasonable range for invoice amounts
                            number_candidates.append({
                                "value": amount_value,
                                "confidence": confidence * 0.4,  # Lower confidence for heuristic matches
                                "source_text": text
                            })
                    except ValueError:
                        continue

            if number_candidates:
                # Pick the largest reasonable amount with decent confidence
                fallback_candidate = max(number_candidates, key=lambda x: x["value"] * x["confidence"])
                best_match = {
                    "value": fallback_candidate["value"],
                    "confidence": fallback_candidate["confidence"]
                }
                logger.info(f"Fallback amount selected: {fallback_candidate['value']} from '{fallback_candidate['source_text']}'")

        return best_match

    def _extract_line_items(self, text_regions: List[Dict], full_text: str) -> List[Dict[str, Any]]:
        """Extract line items from text regions."""
        line_items = []

        # Simple line item extraction - look for text with amounts
        amount_pattern = r'([0-9,]+\.?\d*)\s*(?:บาท)?'

        for region in text_regions:
            text = region["text"]
            confidence = region["confidence"]

            # Look for amounts in the text
            amount_matches = re.findall(amount_pattern, text)
            if amount_matches and confidence > 0.6:
                # Remove the amount from text to get description
                description = re.sub(amount_pattern, '', text).strip()

                for amount_str in amount_matches:
                    try:
                        amount = float(amount_str.replace(",", ""))
                        if amount > 0 and description:
                            line_items.append({
                                "description": {"value": description, "confidence": confidence},
                                "amount": {"value": amount, "confidence": confidence}
                            })
                    except ValueError:
                        continue

        return line_items[:10]  # Limit to 10 line items