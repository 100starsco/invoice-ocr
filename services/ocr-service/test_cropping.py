#!/usr/bin/env python3
"""
Test script for invoice cropping functionality
Tests the crop_invoice_document method with the KBank receipt image
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
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_cropping():
    # Path to the KBank receipt image
    image_path = "/tmp/debug_images/3e92c266-3042-4a8a-aed8-fe6cf642fdbb/00_original.jpg"

    if not os.path.exists(image_path):
        print(f"Error: Test image not found at {image_path}")
        return

    print(f"Loading test image: {image_path}")

    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print("Error: Could not load image")
        return

    print(f"Loaded image shape: {image.shape}")

    # Create ImageProcessor instance
    processor = ImageProcessor()
    processor.enable_debug = True  # Enable debug image saving

    print("Testing crop_invoice_document method...")

    # Test the cropping functionality
    try:
        cropped_image, metadata = processor.crop_invoice_document(image, "test_job")

        print("\n=== CROPPING RESULTS ===")
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
            output_path = "/tmp/test_cropped_result.jpg"
            cv2.imwrite(output_path, cropped_image)
            print(f"Cropped result saved to: {output_path}")
        else:
            print("Cropping was not applied")
            if 'error' in metadata:
                print(f"Error: {metadata['error']}")

    except Exception as e:
        print(f"Error during cropping test: {str(e)}")
        import traceback
        traceback.print_exc()

def test_edge_detection():
    # Path to the KBank receipt image
    image_path = "/tmp/debug_images/3e92c266-3042-4a8a-aed8-fe6cf642fdbb/00_original.jpg"

    if not os.path.exists(image_path):
        print(f"Error: Test image not found at {image_path}")
        return

    print(f"Loading test image for edge detection: {image_path}")

    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print("Error: Could not load image")
        return

    print(f"Loaded image shape: {image.shape}")

    # Create ImageProcessor instance
    processor = ImageProcessor()

    print("Testing detect_document_edges method...")

    # Test edge detection directly
    try:
        corners = processor.detect_document_edges(image, "test_job")

        print("\n=== EDGE DETECTION RESULTS ===")
        print(f"Corners found: {corners}")
        print(f"Corners type: {type(corners)}")
        if corners is not None:
            print(f"Number of corners: {len(corners)}")
            print(f"Corner coordinates: {corners}")

            # Visualize the detected edges
            if len(corners) == 4:
                debug_image = image.copy()
                corners_array = np.array(corners, dtype=np.int32)
                cv2.polylines(debug_image, [corners_array], True, (0, 255, 0), 3)

                # Mark each corner
                for i, corner in enumerate(corners):
                    cv2.circle(debug_image, tuple(map(int, corner)), 10, (0, 0, 255), -1)
                    cv2.putText(debug_image, str(i), (int(corner[0])+15, int(corner[1])),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                output_path = "/tmp/test_edge_detection.jpg"
                cv2.imwrite(output_path, debug_image)
                print(f"Edge detection visualization saved to: {output_path}")
        else:
            print("No corners detected")

    except Exception as e:
        print(f"Error during edge detection test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Testing Invoice Cropping Functionality ===\n")

    print("1. Testing edge detection...")
    test_edge_detection()

    print("\n" + "="*50 + "\n")

    print("2. Testing cropping...")
    test_cropping()

    print("\nTest completed!")