#!/usr/bin/env python3
"""
Test script for improved invoice cropping functionality
Tests the enhanced document detection methods with the KBank receipt image
"""

import cv2
import numpy as np
import logging
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.image_processor import ImageProcessor

# Set up logging to see debug messages
logging.basicConfig(
    level=logging.INFO,  # Changed to INFO to see the important messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_improved_cropping():
    # Path to the KBank receipt image
    image_path = "/tmp/debug_images/3e92c266-3042-4a8a-aed8-fe6cf642fdbb/00_original.jpg"

    if not os.path.exists(image_path):
        print(f"Error: Test image not found at {image_path}")
        return

    print(f"=== Testing Improved Invoice Cropping ===")
    print(f"Loading test image: {image_path}")

    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print("Error: Could not load image")
        return

    print(f"Loaded image shape: {image.shape}")

    # Create ImageProcessor instance with debug enabled
    processor = ImageProcessor()
    processor.enable_debug = True

    print("\n=== Testing Enhanced Document Detection ===")

    # Test the improved cropping functionality
    try:
        cropped_image, metadata = processor.crop_invoice_document(image, "enhanced_test")

        print(f"\n=== ENHANCED CROPPING RESULTS ===")
        print(f"Cropping applied: {metadata.get('cropping_applied', False)}")
        print(f"Reason: {metadata.get('reason', 'N/A')}")
        print(f"Original dimensions: {metadata.get('original_dimensions', 'N/A')}")
        print(f"Cropped dimensions: {metadata.get('cropped_dimensions', 'N/A')}")
        print(f"Area reduction: {metadata.get('area_reduction_percent', 'N/A')}%")
        print(f"Processing time: {metadata.get('processing_time', 'N/A')}s")

        if metadata.get('cropping_applied', False):
            print(f"Crop coordinates: {metadata.get('crop_coordinates', {})}")
            print(f"Detected corners: {metadata.get('detected_corners', [])}")

            # Save the result for inspection
            output_path = "/tmp/enhanced_cropped_result.jpg"
            cv2.imwrite(output_path, cropped_image)
            print(f"\n✅ Enhanced cropped result saved to: {output_path}")

            # Calculate how much background was removed
            original_area = image.shape[0] * image.shape[1]
            cropped_area = cropped_image.shape[0] * cropped_image.shape[1]
            area_reduction = ((original_area - cropped_area) / original_area) * 100

            print(f"✅ Successfully reduced image area by {area_reduction:.1f}%")
            print(f"✅ Original size: {image.shape[1]}x{image.shape[0]} pixels")
            print(f"✅ Cropped size: {cropped_image.shape[1]}x{cropped_image.shape[0]} pixels")

            if area_reduction > 20:
                print(f"🎉 EXCELLENT: Significant background removal achieved!")
            elif area_reduction > 10:
                print(f"✅ GOOD: Moderate background removal achieved.")
            else:
                print(f"⚠️  LIMITED: Minimal background removal - may need further tuning.")

        else:
            print("❌ Enhanced cropping was not applied")
            if 'error' in metadata:
                print(f"Error: {metadata['error']}")

            print("\nLet's test the individual detection methods...")

            # Test color segmentation directly
            print(f"\n--- Testing Color Segmentation ---")
            try:
                corners = processor._detect_document_by_color_segmentation(image, "color_test", image.shape[0] * image.shape[1])
                if corners is not None:
                    print(f"✅ Color segmentation found corners: {corners}")
                else:
                    print(f"❌ Color segmentation failed")
            except Exception as e:
                print(f"❌ Color segmentation error: {e}")

            # Test enhanced contours directly
            print(f"\n--- Testing Enhanced Contours ---")
            try:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                corners = processor._detect_document_by_enhanced_contours(gray, "contour_test", image.shape[0] * image.shape[1])
                if corners is not None:
                    print(f"✅ Enhanced contours found corners: {corners}")
                else:
                    print(f"❌ Enhanced contours failed")
            except Exception as e:
                print(f"❌ Enhanced contours error: {e}")

    except Exception as e:
        print(f"❌ Error during enhanced cropping test: {str(e)}")
        import traceback
        traceback.print_exc()

def compare_with_original():
    """Compare the enhanced result with the original cropping"""
    original_path = "/tmp/test_cropped_result.jpg"
    enhanced_path = "/tmp/enhanced_cropped_result.jpg"

    print(f"\n=== COMPARISON WITH ORIGINAL ===")

    if os.path.exists(original_path) and os.path.exists(enhanced_path):
        original = cv2.imread(original_path)
        enhanced = cv2.imread(enhanced_path)

        if original is not None and enhanced is not None:
            print(f"Original crop size: {original.shape[1]}x{original.shape[0]}")
            print(f"Enhanced crop size: {enhanced.shape[1]}x{enhanced.shape[0]}")

            original_area = original.shape[0] * original.shape[1]
            enhanced_area = enhanced.shape[0] * enhanced.shape[1]

            if enhanced_area < original_area:
                improvement = ((original_area - enhanced_area) / original_area) * 100
                print(f"🎉 Enhanced cropping removed {improvement:.1f}% more background!")
            elif enhanced_area > original_area:
                regression = ((enhanced_area - original_area) / original_area) * 100
                print(f"⚠️  Enhanced cropping is {regression:.1f}% larger - may need tuning")
            else:
                print(f"📊 Both methods produced similar results")
        else:
            print("Could not load comparison images")
    else:
        print("Original test results not available for comparison")

if __name__ == "__main__":
    test_improved_cropping()
    compare_with_original()

    print(f"\n=== Debug Images Available ===")
    print(f"Check /tmp/debug_images/enhanced_test/ for detailed debug images")
    print(f"Check /tmp/debug_images/color_test/ for color segmentation debug")
    print(f"Check /tmp/debug_images/contour_test/ for enhanced contour debug")

    print(f"\n=== Test Completed! ===")