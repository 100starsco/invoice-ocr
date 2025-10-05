"""
Storage utilities for uploading files to DigitalOcean Spaces
"""

import os
import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError
import io

logger = logging.getLogger(__name__)


class DigitalOceanSpacesClient:
    """Client for uploading files to DigitalOcean Spaces (S3-compatible)"""

    def __init__(self):
        self.endpoint_url = os.getenv('DO_SPACES_ENDPOINT', 'https://sgp1.digitaloceanspaces.com')
        self.access_key_id = os.getenv('DO_SPACES_ACCESS_KEY_ID')
        self.secret_access_key = os.getenv('DO_SPACES_SECRET_ACCESS_KEY')
        self.bucket_name = os.getenv('DO_SPACES_BUCKET', 'iocr')
        self.region = os.getenv('DO_SPACES_REGION', 'sgp1')

        if not all([self.access_key_id, self.secret_access_key]):
            logger.warning("DigitalOcean Spaces credentials not configured")
            self.client = None
            return

        try:
            self.client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region
            )
            logger.info(f"DigitalOcean Spaces client initialized: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize DigitalOcean Spaces client: {e}")
            self.client = None

    def upload_file_bytes(self, file_bytes: bytes, key: str, content_type: str = 'image/jpeg') -> Optional[str]:
        """
        Upload file bytes to DigitalOcean Spaces

        Args:
            file_bytes: File content as bytes
            key: Object key/path in the bucket
            content_type: MIME type of the file

        Returns:
            Public URL if successful, None otherwise
        """
        if not self.client:
            logger.error("DigitalOcean Spaces client not available")
            return None

        try:
            # Upload the file
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
                ACL='public-read'  # Make the file publicly accessible
            )

            # Generate public URL
            public_url = f"{self.endpoint_url}/{self.bucket_name}/{key}"
            logger.info(f"Successfully uploaded to DigitalOcean Spaces: {key}")
            return public_url

        except ClientError as e:
            logger.error(f"Failed to upload to DigitalOcean Spaces: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            return None

    def upload_local_file(self, local_path: str, key: str, content_type: str = 'image/jpeg') -> Optional[str]:
        """
        Upload a local file to DigitalOcean Spaces

        Args:
            local_path: Path to local file
            key: Object key/path in the bucket
            content_type: MIME type of the file

        Returns:
            Public URL if successful, None otherwise
        """
        if not os.path.exists(local_path):
            logger.error(f"Local file not found: {local_path}")
            return None

        try:
            with open(local_path, 'rb') as file_data:
                return self.upload_file_bytes(file_data.read(), key, content_type)
        except Exception as e:
            logger.error(f"Failed to read local file {local_path}: {e}")
            return None

    def delete_object(self, key: str) -> bool:
        """
        Delete an object from DigitalOcean Spaces

        Args:
            key: Object key/path in the bucket

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("DigitalOcean Spaces client not available")
            return False

        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Successfully deleted from DigitalOcean Spaces: {key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete from DigitalOcean Spaces: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during deletion: {e}")
            return False


# Global instance
spaces_client = DigitalOceanSpacesClient()


def upload_enhanced_image(image_bytes: bytes, job_id: str, suffix: str = "") -> Optional[str]:
    """
    Upload enhanced image to DigitalOcean Spaces

    Args:
        image_bytes: Image data as bytes
        job_id: OCR job identifier
        suffix: Optional suffix for the filename

    Returns:
        Public URL if successful, None otherwise
    """
    # Generate key for enhanced images
    key = f"enhanced-images/{job_id}_enhanced{suffix}.jpg"

    return spaces_client.upload_file_bytes(
        file_bytes=image_bytes,
        key=key,
        content_type='image/jpeg'
    )


def upload_local_enhanced_image(local_path: str, job_id: str, suffix: str = "") -> Optional[str]:
    """
    Upload local enhanced image file to DigitalOcean Spaces

    Args:
        local_path: Path to local enhanced image
        job_id: OCR job identifier
        suffix: Optional suffix for the filename

    Returns:
        Public URL if successful, None otherwise
    """
    # Generate key for enhanced images
    key = f"enhanced-images/{job_id}_enhanced{suffix}.jpg"

    return spaces_client.upload_local_file(
        local_path=local_path,
        key=key,
        content_type='image/jpeg'
    )