"""
Image Processor

Image preprocessing and enhancement functionality using OpenCV.
"""

from typing import Tuple, Optional, List, Dict, Any, Union
import numpy as np
import requests
import io
import logging
import time
from PIL import Image, ExifTags
import cv2
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Image processor for preprocessing invoice images before OCR.

    Handles image enhancement, noise reduction, and geometric corrections.
    """

    def __init__(self, enable_debug=True, debug_path="/tmp/debug_images"):
        """Initialize image processor."""
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        self.max_download_size = 50 * 1024 * 1024  # 50MB
        self.enable_debug = enable_debug
        self.debug_path = debug_path

        # Create debug directory if enabled
        if self.enable_debug:
            import os
            os.makedirs(self.debug_path, exist_ok=True)

    def load_image_from_url(self, image_url: str) -> np.ndarray:
        """
        Download and load image from URL.

        Args:
            image_url: URL of the image to download

        Returns:
            Image as OpenCV numpy array

        Raises:
            ValueError: If image cannot be loaded or is invalid
        """
        try:
            logger.info(f"Downloading image from URL: {image_url}")

            # Download image with size limit
            response = requests.get(image_url, stream=True, timeout=30)
            response.raise_for_status()

            # Check content length
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_download_size:
                raise ValueError(f"Image too large: {content_length} bytes")

            # Read image data
            image_data = b""
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                downloaded += len(chunk)
                if downloaded > self.max_download_size:
                    raise ValueError(f"Image too large: {downloaded} bytes")
                image_data += chunk

            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(image_data))

            # Convert PIL to OpenCV format
            cv_image = self.pil_to_cv2(pil_image)

            logger.info(f"Successfully loaded image: {cv_image.shape}")
            return cv_image

        except requests.RequestException as e:
            raise ValueError(f"Failed to download image: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to load image: {str(e)}")

    def pil_to_cv2(self, pil_image: Image.Image) -> np.ndarray:
        """
        Convert PIL Image to OpenCV format.

        Args:
            pil_image: PIL Image object

        Returns:
            OpenCV image array (BGR format)
        """
        # Handle different PIL modes
        if pil_image.mode == 'RGBA':
            # Convert RGBA to RGB
            rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
            rgb_image.paste(pil_image, mask=pil_image.split()[-1])
            pil_image = rgb_image
        elif pil_image.mode not in ('RGB', 'L'):
            # Convert other modes to RGB
            pil_image = pil_image.convert('RGB')

        # Convert to numpy array
        numpy_image = np.array(pil_image)

        # Convert RGB to BGR for OpenCV (if color image)
        if len(numpy_image.shape) == 3:
            opencv_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
        else:
            opencv_image = numpy_image

        return opencv_image

    def cv2_to_pil(self, cv2_image: np.ndarray) -> Image.Image:
        """
        Convert OpenCV image to PIL format.

        Args:
            cv2_image: OpenCV image array

        Returns:
            PIL Image object
        """
        # Convert BGR to RGB for PIL (if color image)
        if len(cv2_image.shape) == 3:
            rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = cv2_image

        return Image.fromarray(rgb_image)

    def correct_image_orientation(self, pil_image: Image.Image) -> Image.Image:
        """
        Correct image orientation based on EXIF data.

        Args:
            pil_image: PIL Image with potential EXIF orientation

        Returns:
            Orientation-corrected PIL Image
        """
        try:
            # Get EXIF data
            if not hasattr(pil_image, '_getexif') or pil_image._getexif() is None:
                return pil_image

            exif = pil_image._getexif()
            if not exif:
                return pil_image

            # Find orientation tag
            orientation_key = None
            for key, value in ExifTags.TAGS.items():
                if value == 'Orientation':
                    orientation_key = key
                    break

            if orientation_key is None or orientation_key not in exif:
                return pil_image

            orientation = exif[orientation_key]

            # Apply rotation based on orientation
            if orientation == 2:
                pil_image = pil_image.transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation == 3:
                pil_image = pil_image.rotate(180, expand=True)
            elif orientation == 4:
                pil_image = pil_image.transpose(Image.FLIP_TOP_BOTTOM)
            elif orientation == 5:
                pil_image = pil_image.transpose(Image.FLIP_LEFT_RIGHT).rotate(90, expand=True)
            elif orientation == 6:
                pil_image = pil_image.rotate(270, expand=True)
            elif orientation == 7:
                pil_image = pil_image.transpose(Image.FLIP_LEFT_RIGHT).rotate(270, expand=True)
            elif orientation == 8:
                pil_image = pil_image.rotate(90, expand=True)

            logger.info(f"Applied EXIF orientation correction: {orientation}")

        except Exception as e:
            logger.warning(f"Failed to apply EXIF orientation: {str(e)}")

        return pil_image

    def preprocess_image(
        self,
        image: np.ndarray,
        operations: Optional[List[str]] = None,
        job_id: str = "unknown"
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Apply preprocessing operations to image.

        Args:
            image: Input image as numpy array
            operations: List of preprocessing operations to apply

        Returns:
            Tuple of (preprocessed image, metadata)
        """
        if operations is None:
            operations = ['resize', 'denoise', 'enhance_contrast', 'deskew', 'perspective_correct', 'sharpen', 'threshold']

        processed_image = image.copy()
        metadata = {
            'original_shape': image.shape,
            'operations_applied': [],
            'quality_before': self.get_image_quality_score(image),
            'skew_angle': 0,
            'perspective_corrected': False
        }

        logger.info(f"Starting preprocessing with operations: {operations}")

        # Save original image for debug
        self.save_debug_image(processed_image, job_id, "00_original", metadata['quality_before'])

        # Track failed operations for fallback strategies
        failed_operations = []

        try:
            # 1. Resize to optimal dimensions
            if 'resize' in operations:
                try:
                    processed_image = self.resize_image(processed_image)
                    metadata['operations_applied'].append('resize')
                    self.save_debug_image(processed_image, job_id, "01_resized")
                    logger.info(f"Job {job_id}: Resize operation completed successfully")
                except Exception as e:
                    logger.warning(f"Job {job_id}: Resize operation failed: {str(e)}, continuing with original size")
                    failed_operations.append(('resize', str(e)))

            # 1.5. Crop to invoice document boundaries
            if 'crop_invoice' in operations:
                logger.info(f"Job {job_id}: Entering crop_invoice operation")
                try:
                    processed_image, crop_metadata = self.crop_invoice_document(processed_image, job_id)
                    metadata.update(crop_metadata)
                    if crop_metadata.get('cropping_applied', False):
                        metadata['operations_applied'].append('crop_invoice')
                        logger.info(f"Job {job_id}: Cropping applied successfully")
                        self.save_debug_image(processed_image, job_id, "01.5_cropped_invoice", crop_metadata)
                    else:
                        logger.warning(f"Job {job_id}: Cropping skipped: {crop_metadata.get('reason', 'unknown')}")
                        self.save_debug_image(processed_image, job_id, "01.5_crop_skipped", crop_metadata)
                    logger.info(f"Job {job_id}: Completed crop_invoice operation")
                except Exception as crop_error:
                    logger.error(f"Job {job_id}: Error in crop_invoice operation: {str(crop_error)}")
                    raise
            else:
                logger.info(f"Job {job_id}: crop_invoice not in operations list: {operations}")

            # 2. Denoise
            if 'denoise' in operations:
                try:
                    processed_image = self.denoise_image(processed_image)
                    metadata['operations_applied'].append('denoise')
                    self.save_debug_image(processed_image, job_id, "02_denoised")
                    logger.info(f"Job {job_id}: Denoise operation completed successfully")
                except Exception as e:
                    logger.warning(f"Job {job_id}: Denoise operation failed: {str(e)}, skipping denoising")
                    failed_operations.append(('denoise', str(e)))

            # 3. Enhance contrast
            if 'enhance_contrast' in operations:
                try:
                    processed_image = self.enhance_contrast(processed_image)
                    metadata['operations_applied'].append('enhance_contrast')
                    self.save_debug_image(processed_image, job_id, "03_contrast_enhanced")
                    logger.info(f"Job {job_id}: Contrast enhancement completed successfully")
                except Exception as e:
                    logger.warning(f"Job {job_id}: Contrast enhancement failed: {str(e)}, trying basic histogram equalization fallback")
                    try:
                        # Fallback: basic histogram equalization
                        if len(processed_image.shape) == 3:
                            yuv = cv2.cvtColor(processed_image, cv2.COLOR_BGR2YUV)
                            yuv[:,:,0] = cv2.equalizeHist(yuv[:,:,0])
                            processed_image = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
                        else:
                            processed_image = cv2.equalizeHist(processed_image)
                        metadata['operations_applied'].append('enhance_contrast_fallback')
                        self.save_debug_image(processed_image, job_id, "03_contrast_fallback")
                        logger.info(f"Job {job_id}: Contrast enhancement fallback successful")
                    except Exception as fallback_e:
                        logger.warning(f"Job {job_id}: Contrast enhancement fallback also failed: {str(fallback_e)}, skipping")
                        failed_operations.append(('enhance_contrast', f"{str(e)} | fallback: {str(fallback_e)}"))

            # 4. Detect and correct perspective
            if 'perspective_correct' in operations:
                processed_image, perspective_metadata = self.correct_perspective_with_metadata(processed_image, job_id=job_id)
                metadata.update(perspective_metadata)
                if perspective_metadata.get('perspective_corrected'):
                    metadata['operations_applied'].append('perspective_correct')
                    self.save_debug_image(processed_image, job_id, "04_perspective_corrected", perspective_metadata)
                else:
                    self.save_debug_image(processed_image, job_id, "04_perspective_unchanged", perspective_metadata)

            # 5. Deskew
            if 'deskew' in operations:
                processed_image, skew_angle = self.deskew_image_with_angle(processed_image)
                metadata['skew_angle'] = skew_angle
                skew_metadata = {'skew_angle': skew_angle}
                if abs(skew_angle) > 0.5:  # Only record if significant correction
                    metadata['operations_applied'].append('deskew')
                    self.save_debug_image(processed_image, job_id, "05_deskewed", skew_metadata)
                else:
                    self.save_debug_image(processed_image, job_id, "05_deskew_unchanged", skew_metadata)

            # 6. Sharpen
            if 'sharpen' in operations:
                try:
                    processed_image = self.sharpen_image(processed_image)
                    metadata['operations_applied'].append('sharpen')
                    self.save_debug_image(processed_image, job_id, "06_sharpened")
                    logger.info(f"Job {job_id}: Sharpening completed successfully")
                except Exception as e:
                    logger.warning(f"Job {job_id}: Sharpening operation failed: {str(e)}, trying basic kernel sharpening fallback")
                    try:
                        # Fallback: basic unsharp mask
                        kernel = np.array([[-1,-1,-1],
                                         [-1, 9,-1],
                                         [-1,-1,-1]])
                        processed_image = cv2.filter2D(processed_image, -1, kernel)
                        metadata['operations_applied'].append('sharpen_fallback')
                        self.save_debug_image(processed_image, job_id, "06_sharpen_fallback")
                        logger.info(f"Job {job_id}: Sharpening fallback successful")
                    except Exception as fallback_e:
                        logger.warning(f"Job {job_id}: Sharpening fallback also failed: {str(fallback_e)}, skipping")
                        failed_operations.append(('sharpen', f"{str(e)} | fallback: {str(fallback_e)}"))

            # 7. Apply threshold for better text clarity
            if 'threshold' in operations:
                try:
                    processed_image = self.apply_threshold(processed_image, threshold_type='adaptive')
                    metadata['operations_applied'].append('threshold')
                    self.save_debug_image(processed_image, job_id, "07_thresholded")
                    logger.info(f"Job {job_id}: Adaptive threshold completed successfully")
                except Exception as e:
                    logger.warning(f"Job {job_id}: Adaptive threshold failed: {str(e)}, trying Otsu threshold fallback")
                    try:
                        # Fallback: Otsu's threshold
                        if len(processed_image.shape) == 3:
                            gray = cv2.cvtColor(processed_image, cv2.COLOR_BGR2GRAY)
                        else:
                            gray = processed_image.copy()
                        _, threshold_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                        # Convert back to original format
                        if len(processed_image.shape) == 3:
                            processed_image = cv2.cvtColor(threshold_img, cv2.COLOR_GRAY2BGR)
                        else:
                            processed_image = threshold_img

                        metadata['operations_applied'].append('threshold_otsu_fallback')
                        self.save_debug_image(processed_image, job_id, "07_threshold_otsu_fallback")
                        logger.info(f"Job {job_id}: Otsu threshold fallback successful")
                    except Exception as fallback_e:
                        logger.warning(f"Job {job_id}: Threshold fallback also failed: {str(fallback_e)}, skipping")
                        failed_operations.append(('threshold', f"{str(e)} | fallback: {str(fallback_e)}"))

            # Calculate final quality
            metadata['quality_after'] = self.get_image_quality_score(processed_image)
            metadata['processed_shape'] = processed_image.shape
            metadata['failed_operations'] = failed_operations

            # Save final result
            self.save_debug_image(processed_image, job_id, "08_final", metadata['quality_after'])

            # Log preprocessing summary
            logger.info(f"Job {job_id}: Preprocessing completed. Applied: {metadata['operations_applied']}")
            if failed_operations:
                logger.warning(f"Job {job_id}: Failed operations: {[op[0] for op in failed_operations]}")
                logger.warning(f"Job {job_id}: Processing continued with {len(metadata['operations_applied'])} successful operations")
            logger.info(f"Job {job_id}: Quality improvement: {metadata['quality_before']['overall']:.3f} -> {metadata['quality_after']['overall']:.3f}")

            # Assess if minimum processing was achieved
            critical_operations = ['resize', 'enhance_contrast', 'threshold']
            successful_critical = [op for op in critical_operations if any(op in applied for applied in metadata['operations_applied'])]

            if len(successful_critical) < 1:
                logger.warning(f"Job {job_id}: Very few critical operations succeeded ({successful_critical}), image quality may be poor")
                metadata['processing_quality'] = 'poor'
            elif len(successful_critical) < 2:
                logger.info(f"Job {job_id}: Some critical operations succeeded ({successful_critical}), image quality acceptable")
                metadata['processing_quality'] = 'acceptable'
            else:
                logger.info(f"Job {job_id}: Most critical operations succeeded ({successful_critical}), image quality good")
                metadata['processing_quality'] = 'good'

            return processed_image, metadata

        except Exception as e:
            logger.error(f"Preprocessing failed: {str(e)}")
            return image, {'error': str(e), 'operations_applied': metadata['operations_applied']}

    def enhance_contrast(
        self,
        image: np.ndarray,
        clip_limit: float = 2.0,
        tile_grid_size: Tuple[int, int] = (8, 8)
    ) -> np.ndarray:
        """
        Enhance image contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).

        Args:
            image: Input image
            clip_limit: Threshold for contrast limiting
            tile_grid_size: Size of the grid for histogram equalization

        Returns:
            Contrast-enhanced image
        """
        try:
            # Convert to LAB color space for better contrast enhancement
            if len(image.shape) == 3:
                lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                l_channel, a_channel, b_channel = cv2.split(lab_image)

                # Apply CLAHE to L channel
                clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
                l_channel_clahe = clahe.apply(l_channel)

                # Merge channels and convert back to BGR
                enhanced_lab = cv2.merge([l_channel_clahe, a_channel, b_channel])
                enhanced_image = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
            else:
                # Grayscale image
                clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
                enhanced_image = clahe.apply(image)

            return enhanced_image

        except Exception as e:
            logger.warning(f"Contrast enhancement failed: {str(e)}")
            return image

    def denoise_image(
        self,
        image: np.ndarray,
        filter_strength: int = 10,
        template_window_size: int = 7,
        search_window_size: int = 21
    ) -> np.ndarray:
        """
        Remove noise from image using Non-Local Means denoising.

        Args:
            image: Input image
            filter_strength: Filter strength for noise removal
            template_window_size: Size of template patch for comparison
            search_window_size: Size of search window

        Returns:
            Denoised image
        """
        try:
            if len(image.shape) == 3:
                # Color image
                denoised = cv2.fastNlMeansDenoisingColored(
                    image,
                    None,
                    float(filter_strength),
                    float(filter_strength),
                    template_window_size,
                    search_window_size
                )
            else:
                # Grayscale image
                denoised = cv2.fastNlMeansDenoising(
                    image,
                    None,
                    float(filter_strength),
                    template_window_size,
                    search_window_size
                )

            return denoised

        except Exception as e:
            logger.warning(f"Denoising failed: {str(e)}")
            # Fallback to bilateral filter
            try:
                return cv2.bilateralFilter(image, 9, 75, 75)
            except:
                return image

    def deskew_image(
        self,
        image: np.ndarray,
        angle_threshold: float = 15.0
    ) -> np.ndarray:
        """
        Correct image skew/rotation.

        Args:
            image: Input image
            angle_threshold: Maximum angle to correct (degrees)

        Returns:
            Deskewed image
        """
        deskewed, _ = self.deskew_image_with_angle(image, angle_threshold)
        return deskewed

    def deskew_image_with_angle(
        self,
        image: np.ndarray,
        angle_threshold: float = 15.0
    ) -> Tuple[np.ndarray, float]:
        """
        Correct image skew/rotation and return the angle.

        Args:
            image: Input image
            angle_threshold: Maximum angle to correct (degrees)

        Returns:
            Tuple of (deskewed image, skew angle in degrees)
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Detect lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)

            if lines is None or len(lines) == 0:
                return image, 0.0

            # Calculate angles of detected lines
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle = np.degrees(theta) - 90  # Convert to standard angle

                # Only consider nearly horizontal lines
                if -angle_threshold <= angle <= angle_threshold:
                    angles.append(angle)

            if not angles:
                return image, 0.0

            # Calculate median angle (more robust than mean)
            skew_angle = np.median(angles)

            # Only correct if angle is significant
            if abs(skew_angle) < 0.5:
                return image, skew_angle

            # Apply rotation
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, skew_angle, 1.0)

            # Calculate new image size to avoid clipping
            cos_angle = abs(rotation_matrix[0, 0])
            sin_angle = abs(rotation_matrix[0, 1])
            new_w = int((h * sin_angle) + (w * cos_angle))
            new_h = int((h * cos_angle) + (w * sin_angle))

            # Adjust translation
            rotation_matrix[0, 2] += (new_w / 2) - center[0]
            rotation_matrix[1, 2] += (new_h / 2) - center[1]

            # Apply transformation
            deskewed = cv2.warpAffine(image, rotation_matrix, (new_w, new_h),
                                    flags=cv2.INTER_CUBIC,
                                    borderMode=cv2.BORDER_CONSTANT,
                                    borderValue=(255, 255, 255))

            logger.info(f"Applied deskew correction: {skew_angle:.2f} degrees")
            return deskewed, skew_angle

        except Exception as e:
            logger.warning(f"Deskewing failed: {str(e)}")
            return image, 0.0

    def is_document_image(
        self,
        image: np.ndarray,
        job_id: str = "unknown"
    ) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Classify whether an image contains a document before intensive processing.
        Uses multiple heuristics to reject non-document images like photos, animals, etc.

        Args:
            image: Input image
            job_id: Job ID for debug logging

        Returns:
            Tuple of (is_document, confidence, analysis_metadata)
        """
        try:
            logger.info(f"Job {job_id}: Starting document classification")

            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            metadata = {
                'text_density': 0.0,
                'edge_density': 0.0,
                'rectangular_features': 0.0,
                'brightness_variance': 0.0,
                'color_variance': 0.0,
                'aspect_ratio_score': 0.0
            }

            # 1. Analyze text-like regions
            text_score = self._analyze_text_regions(gray, metadata)

            # 2. Analyze edge patterns typical of documents
            edge_score = self._analyze_edge_patterns(gray, metadata)

            # 3. Analyze rectangular/geometric features
            rect_score = self._analyze_rectangular_features(gray, metadata)

            # 4. Analyze brightness and color distribution
            brightness_score = self._analyze_brightness_distribution(image, gray, metadata)

            # 5. Analyze aspect ratio (documents have typical ratios)
            aspect_score = self._analyze_aspect_ratio(image, metadata)

            # Combine scores with weights
            document_confidence = (
                text_score * 0.35 +       # Text regions are most important
                edge_score * 0.25 +       # Edge patterns are key indicators
                rect_score * 0.20 +       # Rectangular features matter
                brightness_score * 0.10 + # Brightness uniformity
                aspect_score * 0.10       # Typical document ratios
            )

            is_document = document_confidence >= 0.25  # Lowered threshold for document classification (was 0.4)

            metadata['final_confidence'] = document_confidence
            metadata['is_document'] = is_document

            logger.info(f"Job {job_id}: Document classification - confidence: {document_confidence:.3f}, is_document: {is_document}")
            logger.info(f"Job {job_id}: Scores - text: {text_score:.2f}, edge: {edge_score:.2f}, rect: {rect_score:.2f}, bright: {brightness_score:.2f}, aspect: {aspect_score:.2f}")

            return is_document, document_confidence, metadata

        except Exception as e:
            logger.error(f"Job {job_id}: Document classification failed: {str(e)}")
            # Default to allowing processing if classification fails
            return True, 0.5, {'error': str(e)}

    def _analyze_text_regions(self, gray: np.ndarray, metadata: Dict[str, Any]) -> float:
        """Analyze density and distribution of text-like regions."""
        try:
            # Apply morphological operations to identify text regions
            kernel_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
            closed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel_rect)

            # Apply threshold to get binary image
            _, binary = cv2.threshold(closed, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Find text-like contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if len(contours) == 0:
                metadata['text_density'] = 0.0
                return 0.0

            # Calculate text region characteristics
            image_area = gray.shape[0] * gray.shape[1]
            total_text_area = sum(cv2.contourArea(cnt) for cnt in contours)
            text_density = total_text_area / image_area

            # Count text-like regions (elongated horizontal shapes)
            text_regions = 0
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if w > h and w > 20 and h > 5:  # Horizontal text-like regions
                    text_regions += 1

            # Score based on text density and region count
            density_score = min(text_density * 10, 1.0)  # Scale to 0-1
            region_score = min(text_regions / 20, 1.0)    # Scale to 0-1

            text_score = (density_score * 0.7 + region_score * 0.3)

            metadata['text_density'] = text_density
            metadata['text_regions'] = text_regions

            return text_score

        except Exception as e:
            logger.warning(f"Text region analysis failed: {str(e)}")
            return 0.0

    def _analyze_edge_patterns(self, gray: np.ndarray, metadata: Dict[str, Any]) -> float:
        """Analyze edge patterns typical of documents vs natural images."""
        try:
            # Apply Canny edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Calculate edge density
            edge_pixels = np.sum(edges > 0)
            total_pixels = edges.shape[0] * edges.shape[1]
            edge_density = edge_pixels / total_pixels

            # Analyze straight lines using Hough transform
            lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=50)

            if lines is None:
                line_score = 0.0
                horizontal_lines = 0
                vertical_lines = 0
            else:
                # Documents typically have many straight horizontal/vertical lines
                horizontal_lines = 0
                vertical_lines = 0

                for line in lines:
                    rho, theta = line[0]
                    angle = np.degrees(theta)

                    # Check for horizontal lines (0° or 180°)
                    if abs(angle) < 15 or abs(angle - 180) < 15:
                        horizontal_lines += 1
                    # Check for vertical lines (90°)
                    elif abs(angle - 90) < 15:
                        vertical_lines += 1

                # Score based on presence of structured lines
                line_score = min((horizontal_lines + vertical_lines) / 20, 1.0)

            # Combine edge density and line structure
            edge_score = (min(edge_density * 5, 1.0) * 0.4 + line_score * 0.6)

            metadata['edge_density'] = edge_density
            metadata['horizontal_lines'] = horizontal_lines
            metadata['vertical_lines'] = vertical_lines

            return edge_score

        except Exception as e:
            logger.warning(f"Edge pattern analysis failed: {str(e)}")
            return 0.0

    def _analyze_rectangular_features(self, gray: np.ndarray, metadata: Dict[str, Any]) -> float:
        """Analyze presence of rectangular shapes and geometric features."""
        try:
            # Find contours for shape analysis
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if len(contours) == 0:
                metadata['rectangular_features'] = 0.0
                return 0.0

            rectangular_shapes = 0
            total_significant_contours = 0

            image_area = gray.shape[0] * gray.shape[1]

            for cnt in contours:
                contour_area = cv2.contourArea(cnt)

                # Only consider significant contours
                if contour_area < image_area * 0.001:  # Less than 0.1% of image
                    continue

                total_significant_contours += 1

                # Approximate contour to polygon
                epsilon = 0.04 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)

                # Check if it's rectangular (4 corners)
                if len(approx) == 4:
                    rectangular_shapes += 1

            # Score based on proportion of rectangular shapes
            if total_significant_contours == 0:
                rect_score = 0.0
            else:
                rect_score = rectangular_shapes / total_significant_contours

            metadata['rectangular_features'] = rect_score
            metadata['total_significant_contours'] = total_significant_contours
            metadata['rectangular_shapes'] = rectangular_shapes

            return rect_score

        except Exception as e:
            logger.warning(f"Rectangular feature analysis failed: {str(e)}")
            return 0.0

    def _analyze_brightness_distribution(self, image: np.ndarray, gray: np.ndarray, metadata: Dict[str, Any]) -> float:
        """Analyze brightness and color distribution patterns."""
        try:
            # Calculate brightness statistics
            mean_brightness = np.mean(gray)
            std_brightness = np.std(gray)

            # Documents typically have:
            # - High brightness (white/light background)
            # - Low variance (uniform background)
            brightness_score = min(mean_brightness / 255.0, 1.0)
            variance_score = max(0.0, 1.0 - (std_brightness / 127.5))

            # Analyze color distribution if color image
            color_score = 0.5  # Default for grayscale
            if len(image.shape) == 3:
                # Documents typically have low color variance
                bgr_std = np.std(image, axis=(0, 1))
                avg_color_std = np.mean(bgr_std)
                color_score = max(0.0, 1.0 - (avg_color_std / 127.5))
                metadata['color_variance'] = avg_color_std

            # Combine brightness and color uniformity
            brightness_final = (brightness_score * 0.4 + variance_score * 0.4 + color_score * 0.2)

            metadata['brightness_variance'] = std_brightness
            metadata['mean_brightness'] = mean_brightness

            return brightness_final

        except Exception as e:
            logger.warning(f"Brightness analysis failed: {str(e)}")
            return 0.0

    def _analyze_aspect_ratio(self, image: np.ndarray, metadata: Dict[str, Any]) -> float:
        """Analyze image aspect ratio for document-like characteristics."""
        try:
            height, width = image.shape[:2]
            aspect_ratio = max(width, height) / min(width, height)

            # Common document aspect ratios:
            # - A4: 1.41 (√2)
            # - Letter: 1.29
            # - Receipts: 1.5 - 4.0 (can be long)
            # - Business cards: 1.75

            # Score based on how close to typical document ratios
            if 1.0 <= aspect_ratio <= 5.0:  # Reasonable document range
                if 1.2 <= aspect_ratio <= 2.0:  # Most common documents
                    aspect_score = 1.0
                elif 1.0 <= aspect_ratio <= 3.5:  # Including receipts
                    aspect_score = 0.8
                else:  # Very long receipts
                    aspect_score = 0.6
            else:
                # Very wide or very square images are less likely documents
                aspect_score = max(0.0, 1.0 - ((aspect_ratio - 5.0) / 10.0))

            metadata['aspect_ratio'] = aspect_ratio
            metadata['aspect_ratio_score'] = aspect_score

            return aspect_score

        except Exception as e:
            logger.warning(f"Aspect ratio analysis failed: {str(e)}")
            return 0.5

    def detect_document_edges(
        self,
        image: np.ndarray,
        job_id: str = "unknown"
    ) -> Optional[np.ndarray]:
        """
        Multi-stage document edge detection optimized for real-world LINE chat images.
        Uses adaptive Canny parameters, multiple detection methods, and fallback strategies.
        Now includes pre-classification to reject non-document images.

        Args:
            image: Input image
            job_id: Job ID for debug logging

        Returns:
            Array of corner points or None if not detected
        """
        try:
            logger.info(f"Job {job_id}: Starting enhanced document edge detection")

            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            image_area = image.shape[0] * image.shape[1]
            logger.info(f"Job {job_id}: Image area: {image_area} pixels ({image.shape[1]}x{image.shape[0]})")

            # Pre-check: Classify if this is likely a document image
            is_document, doc_confidence, doc_metadata = self.is_document_image(image, job_id)

            if not is_document:
                logger.warning(f"Job {job_id}: Image classified as non-document (confidence: {doc_confidence:.3f})")
                logger.info(f"Job {job_id}: Classification details: {doc_metadata}")
                return None
            else:
                logger.info(f"Job {job_id}: Image classified as document (confidence: {doc_confidence:.3f})")

            # Stage 1: Try adaptive Canny edge detection
            corners = self._detect_edges_adaptive_canny(gray, job_id, image_area)
            if corners is not None:
                return corners

            # Stage 1.5: Try color-based document segmentation for handheld receipts
            logger.info(f"Job {job_id}: Canny detection failed, trying color-based document segmentation")
            corners = self._detect_document_by_color_segmentation(image, job_id, image_area)
            if corners is not None:
                return corners

            # Stage 1.6: Try enhanced contour detection with improved filtering
            logger.info(f"Job {job_id}: Color segmentation failed, trying enhanced contour detection")
            corners = self._detect_document_by_enhanced_contours(gray, job_id, image_area)
            if corners is not None:
                return corners

            # Stage 2: Try text region detection as fallback
            logger.info(f"Job {job_id}: Enhanced detection failed, trying text region detection")
            corners = self._detect_document_by_text_regions(gray, job_id, image_area)
            if corners is not None:
                return corners

            # Stage 3: Try morphological operations for boundary enhancement
            logger.info(f"Job {job_id}: Text region detection failed, trying morphological enhancement")
            corners = self._detect_edges_morphological(gray, job_id, image_area)
            if corners is not None:
                return corners

            logger.warning(f"Job {job_id}: All document boundary detection methods failed")
            return None

        except Exception as e:
            logger.error(f"Job {job_id}: Document edge detection failed: {str(e)}")
            return None

    def _detect_edges_adaptive_canny(
        self,
        gray: np.ndarray,
        job_id: str,
        image_area: int
    ) -> Optional[np.ndarray]:
        """
        Adaptive Canny edge detection with multiple parameter sets.
        """
        # Calculate adaptive parameters based on image statistics
        mean_intensity = np.mean(gray)
        std_intensity = np.std(gray)

        logger.info(f"Job {job_id}: Image stats - mean: {mean_intensity:.1f}, std: {std_intensity:.1f}")

        # Define multiple parameter sets from conservative to aggressive
        canny_params = [
            # (low_thresh, high_thresh, kernel_size, description)
            (50, 150, 5, "conservative"),  # Original parameters
            (30, 120, 5, "moderate"),      # Lower thresholds for faint edges
            (20, 100, 7, "aggressive"),    # Even lower + larger kernel
            (int(mean_intensity * 0.5), int(mean_intensity * 1.2), 5, "adaptive-mean"),  # Based on image mean
            (max(10, int(mean_intensity - std_intensity)), int(mean_intensity + std_intensity), 5, "adaptive-std")  # Based on std dev
        ]

        for i, (low, high, kernel_size, desc) in enumerate(canny_params):
            try:
                logger.info(f"Job {job_id}: Trying Canny {desc}: low={low}, high={high}, kernel={kernel_size}")

                # Apply Gaussian blur
                blurred = cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)

                # Apply Canny edge detection
                edges = cv2.Canny(blurred, max(1, low), max(low + 1, high))

                # Save debug image for each attempt
                self.save_debug_image(edges, job_id, f"edges_{i+1}_{desc}")

                # Find contours
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                if len(contours) == 0:
                    logger.debug(f"Job {job_id}: No contours found with {desc} parameters")
                    continue

                # Try to find document boundary with current edge map
                corners = self._find_document_contour(contours, job_id, image_area, f"{desc}_canny")
                if corners is not None:
                    return corners

            except Exception as e:
                logger.warning(f"Job {job_id}: Canny {desc} failed: {str(e)}")
                continue

        return None

    def _detect_document_by_text_regions(
        self,
        gray: np.ndarray,
        job_id: str,
        image_area: int
    ) -> Optional[np.ndarray]:
        """
        Detect document boundaries by analyzing text regions.
        """
        try:
            logger.info(f"Job {job_id}: Detecting document by text regions")

            # Apply morphological operations to identify text regions
            kernel_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
            kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

            # Close operation to connect text regions
            closed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel_rect)

            # Apply threshold to get binary image
            _, binary = cv2.threshold(closed, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Dilate to merge nearby text regions
            dilated = cv2.dilate(binary, kernel_ellipse, iterations=2)

            # Save debug image
            self.save_debug_image(dilated, job_id, "text_regions")

            # Find contours of text regions
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if len(contours) == 0:
                return None

            # Find the largest text region cluster (likely the document)
            largest_contour = max(contours, key=cv2.contourArea)
            contour_area = cv2.contourArea(largest_contour)

            # Check if text region is significant enough
            area_percentage = (contour_area / image_area) * 100
            logger.info(f"Job {job_id}: Largest text region: {contour_area:.0f} ({area_percentage:.1f}%)")

            if area_percentage < 2.0:  # Lower threshold for small receipts
                logger.info(f"Job {job_id}: Text region too small ({area_percentage:.1f}% < 2.0%)")
                return None

            # Get bounding rectangle of text region
            rect = cv2.minAreaRect(largest_contour)
            corners = cv2.boxPoints(rect)
            corners = np.array(corners, dtype=np.float32)

            # Order corners properly
            ordered_corners = self._order_corners(corners)

            # Create debug visualization
            if self.enable_debug:
                debug_image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                cv2.polylines(debug_image, [ordered_corners.astype(np.int32)], True, (0, 255, 255), 3)
                for i, corner in enumerate(ordered_corners):
                    cv2.circle(debug_image, tuple(corner.astype(int)), 8, (0, 0, 255), -1)
                    cv2.putText(debug_image, str(i), tuple(corner.astype(int) + 12),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                self.save_debug_image(debug_image, job_id, "text_region_boundary")

            logger.info(f"Job {job_id}: Document boundary detected via text regions!")
            logger.info(f"Job {job_id}: Corner points: {ordered_corners.tolist()}")

            return ordered_corners

        except Exception as e:
            logger.warning(f"Job {job_id}: Text region detection failed: {str(e)}")
            return None

    def _detect_edges_morphological(
        self,
        gray: np.ndarray,
        job_id: str,
        image_area: int
    ) -> Optional[np.ndarray]:
        """
        Document detection using morphological operations and gradient analysis.
        """
        try:
            logger.info(f"Job {job_id}: Trying morphological edge enhancement")

            # Apply morphological gradient to enhance edges
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            gradient = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)

            # Apply threshold
            _, binary = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Clean up with morphological operations
            kernel_clean = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_clean)

            # Save debug image
            self.save_debug_image(cleaned, job_id, "morphological_edges")

            # Find contours
            contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if len(contours) == 0:
                return None

            # Try to find document contour
            return self._find_document_contour(contours, job_id, image_area, "morphological")

        except Exception as e:
            logger.warning(f"Job {job_id}: Morphological edge detection failed: {str(e)}")
            return None

    def _find_document_contour(
        self,
        contours: list,
        job_id: str,
        image_area: int,
        method_name: str = "standard"
    ) -> Optional[np.ndarray]:
        """
        Find the best document contour from a list of contours.
        """
        # Sort contours by area in descending order
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        logger.info(f"Job {job_id}: Analyzing {len(contours)} contours from {method_name} method")

        # Multiple epsilon values for contour approximation
        epsilon_values = [0.02, 0.03, 0.04, 0.05]  # From precise to coarse

        # Check top contours
        for i, contour in enumerate(contours[:15]):
            contour_area = cv2.contourArea(contour)
            area_percentage = (contour_area / image_area) * 100

            # Skip very small contours (lowered threshold for receipts)
            if area_percentage < 2.0:  # Reduced from 5% to 2%
                continue

            # Try multiple approximation levels
            for eps_multiplier in epsilon_values:
                epsilon = eps_multiplier * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                logger.debug(f"Job {job_id}: Contour {i+1}: {len(approx)} points, area: {contour_area:.0f} ({area_percentage:.1f}%), eps: {eps_multiplier}")

                # Accept rectangles (4 points) or close approximations (5-6 points)
                if 4 <= len(approx) <= 6:
                    if len(approx) > 4:
                        # For 5-6 point contours, try to reduce to 4 points
                        corners = self._reduce_to_rectangle(approx)
                        if corners is None:
                            continue
                    else:
                        corners = approx.reshape(4, 2)

                    # Order corners properly
                    ordered_corners = self._order_corners(corners)

                    # Validate the detected rectangle
                    confidence = self._validate_document_boundary(ordered_corners, contour_area, image_area)

                    logger.info(f"Job {job_id}: Document boundary candidate found! {len(approx)}→4 points, area: {area_percentage:.1f}%, confidence: {confidence:.2f}")

                    # Increased confidence threshold from 0.3 to 0.75 for better document detection
                    if confidence > 0.75:  # Higher confidence threshold for better document detection
                        # Create debug visualization
                        if self.enable_debug:
                            # Get image dimensions from contour bounds
                            x, y, w, h = cv2.boundingRect(contour)
                            canvas_h = max(y + h + 50, 480)
                            canvas_w = max(x + w + 50, 640)
                            debug_image = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)

                            # Draw original contour in blue
                            cv2.drawContours(debug_image, [contour], -1, (255, 0, 0), 2)

                            # Draw approximated contour in green
                            cv2.polylines(debug_image, [ordered_corners.astype(np.int32)], True, (0, 255, 0), 3)

                            # Mark corners
                            for j, corner in enumerate(ordered_corners):
                                cv2.circle(debug_image, tuple(corner.astype(int)), 8, (0, 0, 255), -1)
                                cv2.putText(debug_image, str(j), tuple(corner.astype(int) + 12),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                            # Add confidence text
                            cv2.putText(debug_image, f"{method_name}: {confidence:.2f}", (10, 30),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

                            self.save_debug_image(debug_image, job_id, f"document_detected_{method_name}")

                        logger.info(f"Job {job_id}: Corner points: {ordered_corners.tolist()}")
                        return ordered_corners
                    else:
                        logger.info(f"Job {job_id}: Low confidence boundary rejected ({confidence:.2f} < 0.75)")

        logger.info(f"Job {job_id}: No suitable document boundary found with {method_name} method")
        return None

    def _reduce_to_rectangle(self, approx: np.ndarray) -> Optional[np.ndarray]:
        """
        Reduce a 5-6 point contour to a 4-point rectangle by merging nearby points.
        """
        if len(approx) == 4:
            return approx.reshape(4, 2)

        points = approx.reshape(-1, 2)

        # Calculate distances between consecutive points
        distances = []
        for i in range(len(points)):
            next_i = (i + 1) % len(points)
            dist = np.linalg.norm(points[i] - points[next_i])
            distances.append((dist, i))

        # Sort by distance and remove the shortest edges
        distances.sort()

        # Keep the 4 longest edges by removing points that create short edges
        points_to_keep = set(range(len(points)))

        for dist, point_idx in distances[:len(points) - 4]:
            if len(points_to_keep) > 4:
                points_to_keep.discard(point_idx)

        if len(points_to_keep) == 4:
            final_points = [points[i] for i in sorted(points_to_keep)]
            return np.array(final_points)

        return None

    def _validate_document_boundary(
        self,
        corners: np.ndarray,
        contour_area: float,
        image_area: int
    ) -> float:
        """
        Validate and score a detected document boundary.

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            # Calculate area ratio
            area_ratio = contour_area / image_area

            # Calculate rectangle area from corners
            rect_area = cv2.contourArea(corners.astype(np.int32))

            # Check aspect ratio (documents are usually not extremely wide or tall)
            width = np.linalg.norm(corners[1] - corners[0])
            height = np.linalg.norm(corners[3] - corners[0])
            aspect_ratio = max(width, height) / min(width, height)

            # Check for right angles (corners should be roughly 90 degrees)
            angle_scores = []
            for i in range(4):
                p1 = corners[i]
                p2 = corners[(i + 1) % 4]
                p3 = corners[(i + 2) % 4]

                # Calculate angle at p2
                v1 = p1 - p2
                v2 = p3 - p2

                cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
                angle = np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))

                # Score based on how close to 90 degrees
                angle_score = 1.0 - abs(angle - 90) / 90.0
                angle_scores.append(max(0, angle_score))

            avg_angle_score = np.mean(angle_scores)

            # Combine scores
            area_score = min(1.0, area_ratio * 5)  # Boost small documents
            aspect_score = max(0, 1.0 - (aspect_ratio - 1) / 10)  # Penalize extreme aspect ratios

            confidence = (area_score * 0.4 + avg_angle_score * 0.4 + aspect_score * 0.2)

            return confidence

        except Exception as e:
            logger.warning(f"Boundary validation failed: {str(e)}")
            return 0.0

    def _order_corners(self, corners: np.ndarray) -> np.ndarray:
        """
        Order corners in clockwise order: top-left, top-right, bottom-right, bottom-left.

        Args:
            corners: Array of 4 corner points

        Returns:
            Ordered corner points
        """
        # Calculate center point
        center = np.mean(corners, axis=0)

        # Sort corners by angle from center
        def angle_from_center(point):
            return np.arctan2(point[1] - center[1], point[0] - center[0])

        corners_with_angles = [(corner, angle_from_center(corner)) for corner in corners]
        corners_with_angles.sort(key=lambda x: x[1])

        # Extract sorted corners
        sorted_corners = np.array([corner for corner, _ in corners_with_angles])

        # Ensure proper ordering: top-left, top-right, bottom-right, bottom-left
        # Find top-left (smallest x+y sum)
        sums = sorted_corners.sum(axis=1)
        top_left_idx = np.argmin(sums)

        # Rotate array so top-left is first
        ordered = np.roll(sorted_corners, -top_left_idx, axis=0)

        return ordered

    def correct_perspective(
        self,
        image: np.ndarray,
        corners: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Apply perspective correction to image.

        Args:
            image: Input image
            corners: Document corner points (auto-detect if None)

        Returns:
            Perspective-corrected image
        """
        corrected, _ = self.correct_perspective_with_metadata(image, corners)
        return corrected

    def correct_perspective_with_metadata(
        self,
        image: np.ndarray,
        corners: Optional[np.ndarray] = None,
        job_id: str = "unknown"
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Apply perspective correction and return metadata.

        Args:
            image: Input image
            corners: Document corner points (auto-detect if None)

        Returns:
            Tuple of (corrected image, metadata)
        """
        metadata = {'perspective_corrected': False, 'corners_detected': False}

        try:
            # Detect corners if not provided
            if corners is None:
                corners = self.detect_document_edges(image, job_id)

            if corners is None:
                return image, metadata

            metadata['corners_detected'] = True

            # Calculate dimensions for the corrected image
            # Use the maximum width and height from the detected corners
            widths = [
                np.linalg.norm(corners[0] - corners[1]),  # top edge
                np.linalg.norm(corners[2] - corners[3])   # bottom edge
            ]
            heights = [
                np.linalg.norm(corners[0] - corners[3]),  # left edge
                np.linalg.norm(corners[1] - corners[2])   # right edge
            ]

            max_width = int(max(widths))
            max_height = int(max(heights))

            # Define destination points for rectangle
            dst_corners = np.array([
                [0, 0],                           # top-left
                [max_width - 1, 0],              # top-right
                [max_width - 1, max_height - 1], # bottom-right
                [0, max_height - 1]              # bottom-left
            ], dtype=np.float32)

            # Calculate perspective transformation matrix
            corners_float = corners.astype(np.float32)
            transform_matrix = cv2.getPerspectiveTransform(corners_float, dst_corners)

            # Apply perspective transformation
            corrected = cv2.warpPerspective(image, transform_matrix, (max_width, max_height),
                                          flags=cv2.INTER_CUBIC,
                                          borderMode=cv2.BORDER_CONSTANT,
                                          borderValue=(255, 255, 255))

            metadata['perspective_corrected'] = True
            metadata['corrected_size'] = (max_width, max_height)
            logger.info(f"Applied perspective correction: {image.shape} -> {corrected.shape}")

            return corrected, metadata

        except Exception as e:
            logger.warning(f"Perspective correction failed: {str(e)}")
            return image, metadata

    def resize_image(
        self,
        image: np.ndarray,
        max_width: int = 2048,
        max_height: int = 2048,
        maintain_aspect: bool = True
    ) -> np.ndarray:
        """
        Resize image to optimal dimensions for OCR.

        Args:
            image: Input image
            max_width: Maximum width
            max_height: Maximum height
            maintain_aspect: Whether to maintain aspect ratio

        Returns:
            Resized image
        """
        try:
            h, w = image.shape[:2]

            # If image is already within limits, return as-is
            if w <= max_width and h <= max_height:
                return image

            if maintain_aspect:
                # Calculate scaling factor to fit within bounds
                scale_w = max_width / w
                scale_h = max_height / h
                scale = min(scale_w, scale_h)

                new_width = int(w * scale)
                new_height = int(h * scale)
            else:
                new_width = min(w, max_width)
                new_height = min(h, max_height)

            # Resize using high-quality interpolation
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

            logger.info(f"Resized image: {image.shape} -> {resized.shape}")
            return resized

        except Exception as e:
            logger.warning(f"Image resizing failed: {str(e)}")
            return image

    def sharpen_image(self, image: np.ndarray) -> np.ndarray:
        """
        Sharpen image for better text clarity.

        Args:
            image: Input image

        Returns:
            Sharpened image
        """
        try:
            # Define sharpening kernel (unsharp mask)
            kernel = np.array([
                [-1, -1, -1],
                [-1,  9, -1],
                [-1, -1, -1]
            ])

            # Apply sharpening
            sharpened = cv2.filter2D(image, -1, kernel)

            return sharpened

        except Exception as e:
            logger.warning(f"Image sharpening failed: {str(e)}")
            return image

    def convert_to_grayscale(
        self,
        image: np.ndarray
    ) -> np.ndarray:
        """
        Convert image to grayscale.

        Args:
            image: Input color image

        Returns:
            Grayscale image
        """
        try:
            if len(image.shape) == 3:
                # Convert BGR to grayscale
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                # Already grayscale
                gray = image.copy()

            return gray

        except Exception as e:
            logger.warning(f"Grayscale conversion failed: {str(e)}")
            return image

    def apply_threshold(
        self,
        image: np.ndarray,
        threshold_type: str = "adaptive"
    ) -> np.ndarray:
        """
        Apply thresholding to create binary image.

        Args:
            image: Input image (will be converted to grayscale if needed)
            threshold_type: Type of thresholding ("adaptive", "otsu", "manual")

        Returns:
            Binary image
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            if threshold_type == "adaptive":
                # Adaptive threshold - good for varying lighting
                binary = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 11, 2
                )
            elif threshold_type == "otsu":
                # Otsu's method - automatic threshold selection
                _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            else:  # manual
                # Simple binary threshold
                _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

            return binary

        except Exception as e:
            logger.warning(f"Thresholding failed: {str(e)}")
            return image

    def get_image_quality_score(
        self,
        image: np.ndarray
    ) -> Dict[str, float]:
        """
        Assess image quality metrics.

        Args:
            image: Input image

        Returns:
            Dictionary with quality metrics (sharpness, brightness, contrast)
        """
        try:
            # Convert to grayscale for analysis
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()

            # Calculate sharpness using Laplacian variance
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness = min(laplacian_var / 1000, 1.0)  # Normalize to 0-1

            # Calculate brightness (mean intensity)
            brightness = np.mean(gray) / 255.0

            # Calculate contrast (standard deviation of intensities)
            contrast = np.std(gray) / 127.5  # Normalize to approximately 0-1

            # Calculate overall quality score
            overall_score = (sharpness * 0.4 + brightness * 0.3 + contrast * 0.3)

            return {
                'sharpness': float(sharpness),
                'brightness': float(brightness),
                'contrast': float(contrast),
                'overall': float(overall_score)
            }

        except Exception as e:
            logger.warning(f"Quality assessment failed: {str(e)}")
            return {
                'sharpness': 0.0,
                'brightness': 0.0,
                'contrast': 0.0,
                'overall': 0.0
            }

    def save_image_to_bytes(self, image: np.ndarray, format: str = 'JPEG', quality: int = 95) -> bytes:
        """
        Convert OpenCV image to bytes for upload.

        Args:
            image: OpenCV image array
            format: Output format ('JPEG', 'PNG')
            quality: JPEG quality (1-100)

        Returns:
            Image as bytes
        """
        try:
            # Convert to PIL for better format handling
            pil_image = self.cv2_to_pil(image)

            # Save to bytes buffer
            buffer = io.BytesIO()
            if format.upper() == 'JPEG':
                # Convert to RGB if grayscale for JPEG
                if pil_image.mode == 'L':
                    pil_image = pil_image.convert('RGB')
                pil_image.save(buffer, format='JPEG', quality=quality, optimize=True)
            else:
                pil_image.save(buffer, format=format.upper())

            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Failed to convert image to bytes: {str(e)}")
            raise

    def save_debug_image(self, image: np.ndarray, job_id: str, step_name: str, metadata: dict = None) -> None:
        """
        Save debug image for visual inspection.

        Args:
            image: OpenCV image array
            job_id: Job identifier for organizing debug images
            step_name: Name of the processing step
            metadata: Optional metadata to log
        """
        if not self.enable_debug:
            return

        try:
            import os
            # Create job-specific debug directory
            job_debug_path = os.path.join(self.debug_path, job_id)
            os.makedirs(job_debug_path, exist_ok=True)

            # Generate debug filename
            debug_filename = f"{step_name}.jpg"
            debug_path = os.path.join(job_debug_path, debug_filename)

            # Convert to PIL and save
            pil_image = self.cv2_to_pil(image)

            # Convert to RGB if grayscale for JPEG
            if pil_image.mode == 'L':
                pil_image = pil_image.convert('RGB')

            pil_image.save(debug_path, format='JPEG', quality=95)

            # Log debug info
            shape_str = f"{image.shape[1]}x{image.shape[0]}"
            if len(image.shape) == 3:
                shape_str += f"x{image.shape[2]}"

            logger.info(f"Debug: Saved {step_name} ({shape_str}) -> {debug_path}")

            if metadata:
                logger.info(f"Debug metadata for {step_name}: {metadata}")

        except Exception as e:
            logger.warning(f"Failed to save debug image for {step_name}: {str(e)}")

    def crop_invoice_document(self, image: np.ndarray, job_id: str = None) -> tuple[np.ndarray, dict]:
        """
        Crop image to invoice document boundaries using edge detection.

        This method leverages the existing document edge detection functionality
        to crop the image to only include the invoice document, removing
        background areas and improving OCR accuracy.

        Args:
            image: OpenCV image array (BGR or grayscale)
            job_id: Optional job identifier for debug logging

        Returns:
            Tuple of (cropped_image, metadata) where:
            - cropped_image: Cropped image containing only the invoice document
            - metadata: Dictionary with cropping details and statistics
        """
        if job_id:
            logger.info(f"Job {job_id}: Starting invoice document cropping")

        logger.debug(f"Job {job_id}: Input image shape: {image.shape}")
        start_time = time.time()
        original_shape = image.shape

        try:
            logger.debug(f"Job {job_id}: Calling detect_document_edges...")
            # Detect document edges using existing functionality
            corners = self.detect_document_edges(image, job_id)
            logger.debug(f"Job {job_id}: detect_document_edges returned: {corners}")

            if corners is None:
                logger.warning(f"Job {job_id}: detect_document_edges returned None, using original image")
                return image, {
                    'cropping_applied': False,
                    'reason': 'document_edges_returned_none',
                    'processing_time': time.time() - start_time,
                    'original_dimensions': f"{original_shape[1]}x{original_shape[0]}"
                }

            if len(corners) != 4:
                logger.warning(f"Job {job_id}: detect_document_edges returned {len(corners)} corners instead of 4, using original image")
                return image, {
                    'cropping_applied': False,
                    'reason': f'wrong_corner_count_{len(corners)}',
                    'corners_found': corners.tolist() if hasattr(corners, 'tolist') else str(corners),
                    'processing_time': time.time() - start_time,
                    'original_dimensions': f"{original_shape[1]}x{original_shape[0]}"
                }

            # Sort corners to get proper rectangle coordinates
            # corners are in format [[x,y], [x,y], [x,y], [x,y]]
            logger.debug(f"Job {job_id}: Converting corners to numpy array...")
            corners_array = np.array(corners, dtype=np.float32)
            logger.debug(f"Job {job_id}: Corners array shape: {corners_array.shape}")

            # Calculate bounding rectangle from detected corners
            logger.debug(f"Job {job_id}: Calculating bounding coordinates...")
            x_coords = corners_array[:, 0]
            y_coords = corners_array[:, 1]
            logger.debug(f"Job {job_id}: X coords: {x_coords}, Y coords: {y_coords}")

            # Get bounding box coordinates
            x_min = max(0, int(np.min(x_coords)))
            y_min = max(0, int(np.min(y_coords)))
            x_max = min(image.shape[1], int(np.max(x_coords)))
            y_max = min(image.shape[0], int(np.max(y_coords)))
            logger.debug(f"Job {job_id}: Initial bounding box: ({x_min},{y_min}) to ({x_max},{y_max})")

            # Add small padding to ensure we don't crop too aggressively
            padding = 10
            x_min = max(0, x_min - padding)
            y_min = max(0, y_min - padding)
            x_max = min(image.shape[1], x_max + padding)
            y_max = min(image.shape[0], y_max + padding)
            logger.debug(f"Job {job_id}: Padded bounding box: ({x_min},{y_min}) to ({x_max},{y_max})")

            # Perform the crop
            logger.debug(f"Job {job_id}: Performing crop operation...")
            cropped_image = image[y_min:y_max, x_min:x_max]
            logger.debug(f"Job {job_id}: Cropped image shape: {cropped_image.shape}")

            # Calculate crop statistics
            original_area = original_shape[0] * original_shape[1]
            cropped_area = cropped_image.shape[0] * cropped_image.shape[1]
            area_reduction = ((original_area - cropped_area) / original_area) * 100

            # Prepare metadata
            crop_metadata = {
                'cropping_applied': True,
                'crop_coordinates': {
                    'x_min': x_min, 'y_min': y_min,
                    'x_max': x_max, 'y_max': y_max,
                    'padding_applied': padding
                },
                'original_dimensions': f"{original_shape[1]}x{original_shape[0]}",
                'cropped_dimensions': f"{cropped_image.shape[1]}x{cropped_image.shape[0]}",
                'area_reduction_percent': round(area_reduction, 2),
                'detected_corners': corners,
                'processing_time': time.time() - start_time
            }

            # Save debug image if enabled
            if job_id and self.enable_debug:
                self.save_debug_image(cropped_image, job_id, "05_cropped_invoice", crop_metadata)

                # Also save overlay with detected corners for debugging
                debug_overlay = image.copy()
                cv2.polylines(debug_overlay, [corners_array.astype(int)], True, (0, 255, 0), 3)
                cv2.rectangle(debug_overlay, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
                self.save_debug_image(debug_overlay, job_id, "05_crop_detection_overlay", crop_metadata)

            logger.info(f"Job {job_id}: Invoice cropped successfully - {area_reduction:.1f}% size reduction")
            return cropped_image, crop_metadata

        except Exception as e:
            logger.error(f"Job {job_id}: Failed to crop invoice document: {str(e)}")
            return image, {
                'cropping_applied': False,
                'reason': 'cropping_error',
                'error': str(e),
                'processing_time': time.time() - start_time,
                'original_dimensions': f"{original_shape[1]}x{original_shape[0]}"
            }

    def _detect_document_by_color_segmentation(
        self,
        image: np.ndarray,
        job_id: str,
        image_area: int
    ) -> Optional[np.ndarray]:
        """
        Robust document detection using color segmentation and clustering.
        Specifically designed for handheld receipts with complex backgrounds.

        Args:
            image: Input color image (BGR)
            job_id: Job identifier for debug logging
            image_area: Total image area in pixels

        Returns:
            Array of corner points or None if not detected
        """
        try:
            logger.info(f"Job {job_id}: Starting color-based document segmentation")

            # Convert to different color spaces for analysis
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 1. Create document mask using multiple criteria

            # Criterion 1: Brightness - documents are typically brighter
            brightness_mask = gray > np.mean(gray) + 0.3 * np.std(gray)

            # Criterion 2: Low saturation - documents are typically white/grayish
            saturation_threshold = np.mean(hsv[:, :, 1]) + 0.5 * np.std(hsv[:, :, 1])
            low_saturation_mask = hsv[:, :, 1] < saturation_threshold

            # Criterion 3: High L* value in LAB space - documents are light
            l_channel = lab[:, :, 0]
            light_mask = l_channel > np.mean(l_channel) + 0.2 * np.std(l_channel)

            # Combine all criteria
            document_mask = brightness_mask & low_saturation_mask & light_mask

            # 2. Clean up the mask with morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))

            # Remove noise
            document_mask = cv2.morphologyEx(document_mask.astype(np.uint8), cv2.MORPH_OPEN, kernel)

            # Fill gaps
            document_mask = cv2.morphologyEx(document_mask, cv2.MORPH_CLOSE, kernel)

            # Dilate to ensure we capture document edges
            document_mask = cv2.dilate(document_mask, kernel, iterations=2)

            # Save debug image
            self.save_debug_image(document_mask * 255, job_id, "color_segmentation_mask")

            # 3. Find document contours
            contours, _ = cv2.findContours(document_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if len(contours) == 0:
                logger.info(f"Job {job_id}: No contours found in color segmentation mask")
                return None

            # Collect and score all valid document candidates
            candidates = []

            for contour in contours:
                contour_area = cv2.contourArea(contour)
                area_percentage = (contour_area / image_area) * 100

                logger.info(f"Job {job_id}: Analyzing contour with area {area_percentage:.1f}%")

                # Skip very small or very large contours
                if area_percentage < 5.0 or area_percentage > 95.0:
                    continue

                # Approximate contour to polygon
                perimeter = cv2.arcLength(contour, True)
                epsilon = 0.02 * perimeter  # Start with looser approximation
                approx = cv2.approxPolyDP(contour, epsilon, True)

                # Try different epsilon values to get a quadrilateral
                for eps_factor in [0.02, 0.03, 0.04, 0.05]:
                    epsilon = eps_factor * perimeter
                    approx = cv2.approxPolyDP(contour, epsilon, True)

                    if len(approx) == 4:
                        break
                    elif len(approx) < 4:
                        # Too simplified, try smaller epsilon
                        continue
                    else:
                        # Too many points, continue with larger epsilon
                        continue

                if len(approx) == 4:
                    corners = approx.reshape(4, 2).astype(np.float32)
                    ordered_corners = self._order_corners(corners)

                    # Validate the detected quadrilateral
                    confidence = self._validate_document_boundary(ordered_corners, contour_area, image_area)

                    if confidence > 0.3:  # Lower threshold for initial filtering
                        # Score this candidate using multiple criteria
                        scores = self._score_document_candidate(
                            contour, ordered_corners, image.shape, job_id
                        )

                        logger.info(f"Job {job_id}: Candidate score {scores['total']:.3f} "
                                  f"(pos:{scores['position']:.2f}, asp:{scores['aspect']:.2f}, "
                                  f"size:{scores['size']:.2f}, comp:{scores['compactness']:.2f}, "
                                  f"border:{scores['border']:.2f})")

                        candidates.append({
                            'contour': contour,
                            'corners': ordered_corners,
                            'confidence': confidence,
                            'scores': scores
                        })

                else:
                    logger.info(f"Job {job_id}: Contour approximation failed, points: {len(approx)}")

            # Sort candidates by total score (best first)
            candidates.sort(key=lambda x: x['scores']['total'], reverse=True)

            # Select the best candidate
            for candidate in candidates:
                contour = candidate['contour']
                ordered_corners = candidate['corners']
                confidence = candidate['confidence']
                scores = candidate['scores']

                logger.info(f"Job {job_id}: Evaluating candidate with total score: {scores['total']:.3f}, "
                          f"confidence: {confidence:.2f}")

                # Accept candidate if it has good total score and acceptable confidence
                if scores['total'] > 0.4 and confidence > 0.5:
                    # Create debug visualization
                    if self.enable_debug:
                        debug_image = image.copy()
                        cv2.drawContours(debug_image, [contour], -1, (255, 0, 0), 3)
                        cv2.polylines(debug_image, [ordered_corners.astype(np.int32)], True, (0, 255, 0), 4)

                        # Mark corners
                        for i, corner in enumerate(ordered_corners):
                            cv2.circle(debug_image, tuple(corner.astype(int)), 10, (0, 0, 255), -1)
                            cv2.putText(debug_image, str(i), tuple(corner.astype(int) + 15),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

                        # Add score information
                        cv2.putText(debug_image, f"Score: {scores['total']:.3f}", (10, 30),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)
                        cv2.putText(debug_image, f"Conf: {confidence:.2f}", (10, 70),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)

                        # Add individual scores
                        score_text = (f"P:{scores['position']:.2f} A:{scores['aspect']:.2f} "
                                    f"S:{scores['size']:.2f} C:{scores['compactness']:.2f} B:{scores['border']:.2f}")
                        cv2.putText(debug_image, score_text, (10, 110),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

                        self.save_debug_image(debug_image, job_id, "color_segmentation_result")

                    logger.info(f"Job {job_id}: Document detected by color segmentation with multi-criteria scoring!")
                    return ordered_corners

            # Log information about rejected candidates
            if candidates:
                best_candidate = candidates[0]
                logger.info(f"Job {job_id}: Best candidate had score {best_candidate['scores']['total']:.3f} "
                          f"but didn't meet thresholds (score > 0.4, confidence > 0.5)")
            else:
                logger.info(f"Job {job_id}: No valid quadrilateral candidates found")

            logger.info(f"Job {job_id}: Color segmentation failed to find document")
            return None

        except Exception as e:
            logger.warning(f"Job {job_id}: Color segmentation failed: {str(e)}")
            return None

    def _detect_document_by_enhanced_contours(
        self,
        gray: np.ndarray,
        job_id: str,
        image_area: int
    ) -> Optional[np.ndarray]:
        """
        Enhanced contour detection with improved preprocessing and filtering.
        Uses adaptive thresholding and advanced contour analysis.

        Args:
            gray: Input grayscale image
            job_id: Job identifier for debug logging
            image_area: Total image area in pixels

        Returns:
            Array of corner points or None if not detected
        """
        try:
            logger.info(f"Job {job_id}: Starting enhanced contour detection")

            # 1. Advanced preprocessing pipeline

            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Adaptive thresholding for better edge definition
            adaptive_thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Morphological operations to connect nearby edges
            kernel_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

            # Close gaps in edges
            closed = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel_rect)

            # Remove noise
            cleaned = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_ellipse)

            # Edge detection with multiple methods
            edges_list = []

            # Sobel edge detection
            sobelx = cv2.Sobel(cleaned, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(cleaned, cv2.CV_64F, 0, 1, ksize=3)
            sobel_edges = np.sqrt(sobelx**2 + sobely**2)
            sobel_edges = np.uint8(sobel_edges / sobel_edges.max() * 255)
            edges_list.append(('sobel', sobel_edges))

            # Laplacian edge detection
            laplacian = cv2.Laplacian(cleaned, cv2.CV_64F)
            laplacian_edges = np.uint8(np.absolute(laplacian))
            edges_list.append(('laplacian', laplacian_edges))

            # Canny with adaptive thresholds
            median_val = np.median(cleaned)
            lower = int(max(0, 0.7 * median_val))
            upper = int(min(255, 1.3 * median_val))
            canny_edges = cv2.Canny(cleaned, lower, upper)
            edges_list.append(('canny_adaptive', canny_edges))

            # Save debug images
            for edge_name, edge_img in edges_list:
                self.save_debug_image(edge_img, job_id, f"enhanced_{edge_name}_edges")

            # 2. Analyze each edge detection method
            for edge_name, edges in edges_list:
                logger.info(f"Job {job_id}: Analyzing {edge_name} edges")

                # Find contours
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                if len(contours) == 0:
                    continue

                # Sort contours by area
                contours = sorted(contours, key=cv2.contourArea, reverse=True)

                for i, contour in enumerate(contours[:5]):  # Check top 5 contours
                    contour_area = cv2.contourArea(contour)
                    area_percentage = (contour_area / image_area) * 100

                    # Skip contours that are too small or too large
                    if area_percentage < 8.0 or area_percentage > 90.0:
                        continue

                    # Check contour aspect ratio (documents are typically rectangular)
                    rect = cv2.minAreaRect(contour)
                    width, height = rect[1]
                    if width > 0 and height > 0:
                        aspect_ratio = max(width, height) / min(width, height)
                        if aspect_ratio > 5.0:  # Skip very elongated shapes
                            continue

                    # Approximate contour to polygon with multiple epsilon values
                    perimeter = cv2.arcLength(contour, True)

                    for eps_factor in [0.015, 0.02, 0.025, 0.03, 0.04]:
                        epsilon = eps_factor * perimeter
                        approx = cv2.approxPolyDP(contour, epsilon, True)

                        if len(approx) == 4:
                            corners = approx.reshape(4, 2).astype(np.float32)
                            ordered_corners = self._order_corners(corners)

                            # Enhanced validation
                            confidence = self._validate_document_boundary(ordered_corners, contour_area, image_area)

                            # Additional validation: check if corners form a reasonable rectangle
                            if self._validate_rectangle_shape(ordered_corners):
                                confidence += 0.1  # Bonus for good rectangle shape

                            logger.info(f"Job {job_id}: {edge_name} found quadrilateral (eps={eps_factor:.3f}, conf={confidence:.2f})")

                            if confidence > 0.7:  # Higher threshold for enhanced detection
                                # Create debug visualization
                                if self.enable_debug:
                                    debug_image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                                    cv2.drawContours(debug_image, [contour], -1, (255, 0, 0), 2)
                                    cv2.polylines(debug_image, [ordered_corners.astype(np.int32)], True, (0, 255, 0), 3)

                                    # Mark corners
                                    for j, corner in enumerate(ordered_corners):
                                        cv2.circle(debug_image, tuple(corner.astype(int)), 8, (0, 0, 255), -1)
                                        cv2.putText(debug_image, str(j), tuple(corner.astype(int) + 12),
                                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                                    cv2.putText(debug_image, f"Enhanced {edge_name}: {confidence:.2f}", (10, 30),
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

                                    self.save_debug_image(debug_image, job_id, f"enhanced_{edge_name}_result")

                                logger.info(f"Job {job_id}: Document detected by enhanced {edge_name} detection!")
                                return ordered_corners

                        elif len(approx) < 4:
                            break  # Stop trying smaller epsilon values

            logger.info(f"Job {job_id}: Enhanced contour detection failed")
            return None

        except Exception as e:
            logger.warning(f"Job {job_id}: Enhanced contour detection failed: {str(e)}")
            return None

    def _validate_rectangle_shape(self, corners: np.ndarray) -> bool:
        """
        Validate if the detected corners form a reasonable rectangle shape.

        Args:
            corners: Array of 4 corner points

        Returns:
            True if corners form a good rectangle, False otherwise
        """
        try:
            # Calculate side lengths
            sides = []
            for i in range(4):
                p1 = corners[i]
                p2 = corners[(i + 1) % 4]
                side_length = np.linalg.norm(p2 - p1)
                sides.append(side_length)

            # Check if opposite sides are similar in length
            side_ratios = [
                min(sides[0], sides[2]) / max(sides[0], sides[2]),  # Top/Bottom ratio
                min(sides[1], sides[3]) / max(sides[1], sides[3])   # Left/Right ratio
            ]

            # Both ratios should be reasonably close to 1.0
            if all(ratio > 0.7 for ratio in side_ratios):
                return True

            return False

        except Exception:
            return False

    def _score_document_candidate(
        self,
        contour: np.ndarray,
        corners: np.ndarray,
        image_shape: tuple,
        job_id: str
    ) -> dict:
        """
        Score a document candidate using multiple criteria.

        Args:
            contour: Contour points
            corners: Ordered corner points
            image_shape: (height, width) of image
            job_id: Job identifier for debug logging

        Returns:
            Dictionary with individual scores and total score
        """
        height, width = image_shape[:2]
        image_area = height * width
        contour_area = cv2.contourArea(contour)

        # 1. Position Score (0-1): Favor center-right positioning for handheld receipts
        center_x = np.mean(corners[:, 0])
        center_y = np.mean(corners[:, 1])

        # Optimal position is center-right (0.6 horizontally, 0.5 vertically)
        optimal_x_ratio = 0.6
        optimal_y_ratio = 0.5

        x_ratio = center_x / width
        y_ratio = center_y / height

        x_distance = abs(x_ratio - optimal_x_ratio)
        y_distance = abs(y_ratio - optimal_y_ratio)

        # Position score: higher for positions closer to optimal
        position_score = max(0, 1.0 - 2.0 * (x_distance + y_distance))

        # 2. Aspect Ratio Score (0-1): Favor rectangular shapes (height > width)
        rect_width = max(
            np.linalg.norm(corners[1] - corners[0]),
            np.linalg.norm(corners[2] - corners[3])
        )
        rect_height = max(
            np.linalg.norm(corners[3] - corners[0]),
            np.linalg.norm(corners[2] - corners[1])
        )

        if rect_width > 0:
            aspect_ratio = rect_height / rect_width
            # Optimal aspect ratio for receipts: 1.2 to 3.0 (taller than wide)
            if 1.2 <= aspect_ratio <= 3.0:
                aspect_score = 1.0
            elif aspect_ratio < 1.2:
                # Penalize square/wide rectangles
                aspect_score = max(0, aspect_ratio / 1.2)
            else:
                # Penalize very tall rectangles
                aspect_score = max(0, 3.0 / aspect_ratio)
        else:
            aspect_score = 0

        # 3. Size Score (0-1): Balance between too small and too large
        area_percentage = (contour_area / image_area) * 100

        # Optimal size range: 10-60% of image area
        if 10 <= area_percentage <= 60:
            size_score = 1.0
        elif area_percentage < 10:
            size_score = area_percentage / 10
        else:
            size_score = max(0, (90 - area_percentage) / 30)

        # 4. Compactness Score (0-1): Prefer clean rectangular shapes
        perimeter = cv2.arcLength(contour, True)
        if perimeter > 0:
            # Isoperimetric ratio: 4π * area / perimeter²
            # Perfect rectangle has ratio closer to π/4 ≈ 0.785
            compactness = (4 * np.pi * contour_area) / (perimeter * perimeter)
            # Scale to 0-1 where rectangle-like shapes score higher
            compactness_score = min(1.0, compactness / 0.785)
        else:
            compactness_score = 0

        # 5. Border Distance Score (0-1): Penalize regions too close to image borders
        min_border_distance = min(
            np.min(corners[:, 0]),  # distance from left
            np.min(corners[:, 1]),  # distance from top
            width - np.max(corners[:, 0]),   # distance from right
            height - np.max(corners[:, 1])   # distance from bottom
        )

        # Good document should be at least 5% away from borders
        min_distance_threshold = min(width, height) * 0.05
        if min_border_distance >= min_distance_threshold:
            border_score = 1.0
        else:
            border_score = min_border_distance / min_distance_threshold

        # Weighted total score
        weights = {
            'position': 0.25,    # Important for handheld receipts
            'aspect': 0.20,      # Important for document identification
            'size': 0.20,        # Important for reasonable regions
            'compactness': 0.20, # Important for clean rectangles
            'border': 0.15       # Important to avoid background regions
        }

        total_score = (
            position_score * weights['position'] +
            aspect_score * weights['aspect'] +
            size_score * weights['size'] +
            compactness_score * weights['compactness'] +
            border_score * weights['border']
        )

        return {
            'total': total_score,
            'position': position_score,
            'aspect': aspect_score,
            'size': size_score,
            'compactness': compactness_score,
            'border': border_score,
            'area_percentage': area_percentage,
            'center_position': (x_ratio, y_ratio)
        }