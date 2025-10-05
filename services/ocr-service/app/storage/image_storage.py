"""
Image Storage Service

Hybrid implementation supporting both local storage and DigitalOcean Spaces.
Uses DigitalOcean Spaces when configured, falls back to local storage.
"""

import os
import uuid
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import base64

logger = logging.getLogger(__name__)


class ImageStorageService:
    """
    Image storage service for handling enhanced/processed images.

    This is a placeholder implementation that stores images locally.
    In production, replace with cloud storage integration.
    """

    def __init__(self, storage_path: str = "/tmp/ocr_images"):
        """
        Initialize image storage service.

        Args:
            storage_path: Local storage path for images (fallback)
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Local storage configuration
        self.base_url = os.getenv("IMAGE_STORAGE_BASE_URL", "http://localhost:8001/images")

        # DigitalOcean Spaces configuration
        self.storage_provider = os.getenv("STORAGE_PROVIDER", "local")
        self.spaces_client = None

        if self.storage_provider == "spaces":
            try:
                from ..utils.storage import spaces_client
                self.spaces_client = spaces_client
                if self.spaces_client.client:
                    logger.info("DigitalOcean Spaces storage enabled")
                else:
                    logger.warning("DigitalOcean Spaces client not available, falling back to local storage")
                    self.storage_provider = "local"
            except ImportError as e:
                logger.error(f"Failed to import DigitalOcean Spaces client: {e}")
                self.storage_provider = "local"

    def store_image(
        self,
        image_bytes: bytes,
        job_id: str,
        image_type: str = "enhanced",
        file_extension: str = "jpg"
    ) -> str:
        """
        Store image and return public URL.

        Args:
            image_bytes: Image data as bytes
            job_id: Job identifier for organizing images
            image_type: Type of image (original, enhanced, etc.)
            file_extension: File extension without dot

        Returns:
            Public URL to access the stored image
        """
        try:
            # Try DigitalOcean Spaces first if configured
            if self.storage_provider == "spaces" and self.spaces_client and self.spaces_client.client:
                # Upload to DigitalOcean Spaces
                spaces_url = self._store_to_spaces(image_bytes, job_id, image_type, file_extension)
                if spaces_url:
                    # ALSO save locally for testing/debugging purposes
                    try:
                        local_url = self._store_locally(image_bytes, job_id, image_type, file_extension)
                        logger.info(f"Image saved to both Spaces ({spaces_url}) and locally ({local_url})")
                    except Exception as local_error:
                        logger.warning(f"Failed to save locally while Spaces succeeded: {local_error}")
                    return spaces_url

                logger.warning("DigitalOcean Spaces upload failed, falling back to local storage")

            # Fallback to local storage only
            return self._store_locally(image_bytes, job_id, image_type, file_extension)

        except Exception as e:
            logger.error(f"Failed to store image for job {job_id}: {e}")
            # Return a placeholder URL if all storage methods fail
            return f"{self.base_url}/placeholder_{job_id}_{image_type}.{file_extension}"

    def _store_to_spaces(
        self,
        image_bytes: bytes,
        job_id: str,
        image_type: str,
        file_extension: str
    ) -> Optional[str]:
        """
        Store image to DigitalOcean Spaces.

        Returns:
            Public URL if successful, None otherwise
        """
        try:
            # Generate key for the image
            filename = f"{job_id}_{image_type}_{uuid.uuid4().hex}.{file_extension}"
            key = f"enhanced-images/{filename}"

            # Upload to DigitalOcean Spaces
            public_url = self.spaces_client.upload_file_bytes(
                file_bytes=image_bytes,
                key=key,
                content_type=f'image/{file_extension}'
            )

            if public_url:
                logger.info(f"Successfully uploaded enhanced image to Spaces: {key}")
                return public_url
            else:
                logger.error(f"Failed to upload enhanced image to Spaces: {key}")
                return None

        except Exception as e:
            logger.error(f"Error uploading to Spaces: {e}")
            return None

    def _store_locally(
        self,
        image_bytes: bytes,
        job_id: str,
        image_type: str,
        file_extension: str
    ) -> str:
        """
        Store image locally as fallback.

        Returns:
            Local public URL
        """
        # Generate unique filename
        filename = f"{job_id}_{image_type}_{uuid.uuid4().hex}.{file_extension}"
        file_path = self.storage_path / filename

        # Save image locally
        with open(file_path, 'wb') as f:
            f.write(image_bytes)

        # Generate public URL
        public_url = f"{self.base_url}/{filename}"

        logger.info(f"Stored image locally: {filename}")
        return public_url

    def get_image_path(self, filename: str) -> Optional[Path]:
        """
        Get local file path for an image.

        Args:
            filename: Image filename

        Returns:
            Path to local file or None if not found
        """
        file_path = self.storage_path / filename
        if file_path.exists():
            return file_path
        return None

    def delete_image(self, filename: str) -> bool:
        """
        Delete image from storage.

        Args:
            filename: Image filename to delete

        Returns:
            True if deleted successfully
        """
        try:
            file_path = self.storage_path / filename
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted image {filename}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete image {filename}: {e}")
            return False

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.

        Returns:
            Dictionary with storage statistics
        """
        try:
            files = list(self.storage_path.glob("*"))
            total_files = len(files)
            total_size = sum(f.stat().st_size for f in files if f.is_file())

            return {
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "storage_path": str(self.storage_path)
            }
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "storage_path": str(self.storage_path),
                "error": str(e)
            }


# Global storage service instance
_storage_service = None


def get_storage_service() -> ImageStorageService:
    """
    Get global image storage service instance.

    Returns:
        ImageStorageService instance
    """
    global _storage_service
    if _storage_service is None:
        storage_path = os.getenv("IMAGE_STORAGE_PATH", "/tmp/ocr_images")
        _storage_service = ImageStorageService(storage_path)
    return _storage_service


# Production cloud storage integration example (commented out)
"""
class CloudImageStorageService(ImageStorageService):
    '''Production cloud storage implementation example.'''

    def __init__(self):
        import boto3  # AWS S3 example

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.base_url = f"https://{self.bucket_name}.s3.amazonaws.com"

    def store_image(self, image_bytes: bytes, job_id: str, image_type: str = "enhanced", file_extension: str = "jpg") -> str:
        filename = f"{job_id}_{image_type}_{uuid.uuid4().hex}.{file_extension}"

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=image_bytes,
                ContentType=f'image/{file_extension}'
            )
            return f"{self.base_url}/{filename}"
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            return f"{self.base_url}/error_{filename}"
"""