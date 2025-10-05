"""
Image serving endpoints for stored images.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import logging

from ..storage.image_storage import get_storage_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/images/{filename}")
async def serve_image(filename: str):
    """
    Serve stored image file.

    Args:
        filename: Image filename to serve

    Returns:
        FileResponse with image content
    """
    try:
        # Validate filename to prevent path traversal
        if ".." in filename or "/" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")

        storage_service = get_storage_service()
        file_path = storage_service.get_image_path(filename)

        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")

        # Determine media type based on file extension
        extension = file_path.suffix.lower()
        media_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        media_type = media_type_map.get(extension, 'image/jpeg')

        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve image {filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve image")


@router.get("/images/stats")
async def get_storage_stats():
    """
    Get image storage statistics.

    Returns:
        Storage statistics
    """
    try:
        storage_service = get_storage_service()
        stats = storage_service.get_storage_stats()
        return stats

    except Exception as e:
        logger.error(f"Failed to get storage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get storage stats")