"""
URL conversion utilities for handling image proxy URLs
"""
import re
import os
from typing import Optional

def convert_to_proxy_url(original_url: str) -> str:
    """
    Convert a DigitalOcean Spaces URL to a proxy URL that can be accessed by the OCR service.

    Args:
        original_url: The original DigitalOcean Spaces URL

    Returns:
        str: The proxy URL that can be accessed through the Hono API

    Example:
        https://sgp1.digitaloceanspaces.com/iocr/line-images/U092552e6f814223d05ce3719c09424e5/enhanced_6e6f56a8-4ff2-4c8f-b4b5-199c54877e49.jpg
        becomes:
        http://localhost:3000/api/images/proxy/line-images/U092552e6f814223d05ce3719c09424e5/enhanced_6e6f56a8-4ff2-4c8f-b4b5-199c54877e49.jpg
    """
    # Get the API base URL from environment
    api_base_url = os.getenv('API_BASE_URL', 'http://localhost:3000')

    # Pattern to extract the key from DigitalOcean Spaces URL
    # https://sgp1.digitaloceanspaces.com/iocr/path/to/file.jpg -> path/to/file.jpg
    spaces_pattern = r'https://[^/]+\.digitaloceanspaces\.com/[^/]+/(.+)'

    match = re.match(spaces_pattern, original_url)
    if match:
        # Extract the file path after the bucket name
        file_path = match.group(1)

        # Create the proxy URL
        proxy_url = f"{api_base_url}/api/images/proxy/{file_path}"
        return proxy_url

    # If it doesn't match the DigitalOcean Spaces pattern, return the original URL
    # This handles cases like external URLs or already converted proxy URLs
    return original_url

def is_digitalocean_spaces_url(url: str) -> bool:
    """
    Check if a URL is a DigitalOcean Spaces URL

    Args:
        url: The URL to check

    Returns:
        bool: True if it's a DigitalOcean Spaces URL
    """
    return 'digitaloceanspaces.com' in url

def get_image_filename(url: str) -> Optional[str]:
    """
    Extract the filename from a URL

    Args:
        url: The image URL

    Returns:
        str: The filename, or None if not found
    """
    # Extract filename from URL
    parts = url.split('/')
    if parts:
        return parts[-1]
    return None