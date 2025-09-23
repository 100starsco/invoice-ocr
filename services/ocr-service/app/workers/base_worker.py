"""
Base Worker Class

Base class for all RQ workers with common functionality.
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
import logging
from abc import ABC, abstractmethod

from ..database import RedisClient, MongoDBClient
from ..models import JobStatus, JobType


class BaseWorker(ABC):
    """
    Base class for all worker types.

    Provides common functionality for job processing, status updates,
    and error handling.
    """

    def __init__(
        self,
        worker_id: str,
        redis_client: Optional[RedisClient] = None,
        mongodb_client: Optional[MongoDBClient] = None
    ):
        """
        Initialize base worker.

        Args:
            worker_id: Unique identifier for this worker instance
            redis_client: Redis client for queue operations
            mongodb_client: MongoDB client for result storage
        """
        self.worker_id = worker_id
        self.redis_client = redis_client
        self.mongodb_client = mongodb_client
        self.logger = logging.getLogger(f"worker.{self.__class__.__name__}")

    @abstractmethod
    def process_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a job.

        Args:
            job_data: Job parameters and data

        Returns:
            Processing results

        Raises:
            Exception: If processing fails
        """
        pass

    def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update job status in database.

        Args:
            job_id: Job identifier
            status: New status
            progress: Progress percentage (0-100)
            error_message: Error message if applicable
        """
        # TODO: Implement status update logic
        pass

    def log_job_start(self, job_id: str, job_type: JobType) -> None:
        """
        Log job start and update status.

        Args:
            job_id: Job identifier
            job_type: Type of job
        """
        # TODO: Implement job start logging
        pass

    def log_job_completion(
        self,
        job_id: str,
        result: Dict[str, Any],
        processing_time: float
    ) -> None:
        """
        Log job completion and store results.

        Args:
            job_id: Job identifier
            result: Processing results
            processing_time: Time taken to process (seconds)
        """
        # TODO: Implement completion logging
        pass

    def log_job_error(
        self,
        job_id: str,
        error: Exception,
        retry_count: int = 0
    ) -> None:
        """
        Log job error and update status.

        Args:
            job_id: Job identifier
            error: Exception that occurred
            retry_count: Number of retries attempted
        """
        # TODO: Implement error logging
        pass

    def validate_job_data(self, job_data: Dict[str, Any]) -> bool:
        """
        Validate job data before processing.

        Args:
            job_data: Job parameters to validate

        Returns:
            True if valid, False otherwise
        """
        # TODO: Implement job data validation
        pass

    def should_retry(self, error: Exception, retry_count: int) -> bool:
        """
        Determine if job should be retried.

        Args:
            error: Exception that occurred
            retry_count: Current retry count

        Returns:
            True if job should be retried
        """
        # TODO: Implement retry logic
        pass

    def cleanup_resources(self) -> None:
        """Clean up worker resources."""
        # TODO: Implement resource cleanup
        pass

    def get_worker_stats(self) -> Dict[str, Any]:
        """
        Get worker performance statistics.

        Returns:
            Dictionary with worker statistics
        """
        # TODO: Implement statistics collection
        pass