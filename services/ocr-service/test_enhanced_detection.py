#!/usr/bin/env python3
"""
Test script for enhanced document boundary detection.
Tests the new adaptive Canny edge detection and fallback methods.
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

import cv2
import numpy as np
from app.core.image_processor import ImageProcessor

def test_enhanced_detection():
    """Test the enhanced document detection on existing debug images."""

    # Initialize image processor
    processor = ImageProcessor(enable_debug=True, debug_path="/tmp/test_enhanced_detection")

    # Look for existing test images
    test_image_paths = [
        "/tmp/debug_images/7013d0a1-44ea-4137-83c4-5133c1913ae7/00_original.jpg"
    ]

    for image_path in test_image_paths:
        if os.path.exists(image_path):
            print(f"\n=== Testing enhanced detection on: {image_path} ===")

            # Load the image
            image = cv2.imread(image_path)
            if image is None:
                print(f"Failed to load image: {image_path}")
                continue

            print(f"Image loaded: {image.shape}")

            # Test the enhanced document edge detection
            try:
                corners = processor.detect_document_edges(image, "test_enhanced")

                if corners is not None:
                    print(f"✅ SUCCESS: Document boundary detected!")
                    print(f"Corner points: {corners.tolist()}")

                    # Calculate area
                    contour_area = cv2.contourArea(corners.astype(np.int32))
                    image_area = image.shape[0] * image.shape[1]
                    area_percentage = (contour_area / image_area) * 100
                    print(f"Detected area: {contour_area:.0f} pixels ({area_percentage:.1f}% of image)")

                else:
                    print(f"❌ FAILED: No document boundary detected")

            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print(f"Test image not found: {image_path}")

    # Check what debug files were created
    debug_dir = "/tmp/test_enhanced_detection/test_enhanced"
    if os.path.exists(debug_dir):
        print(f"\n=== Debug files created in {debug_dir} ===")
        debug_files = sorted(os.listdir(debug_dir))
        for f in debug_files:
            file_path = os.path.join(debug_dir, f)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path) / 1024  # KB
                print(f"  {f} ({size:.1f} KB)")

    print(f"\n=== Test completed ===")

if __name__ == "__main__":
    test_enhanced_detection()