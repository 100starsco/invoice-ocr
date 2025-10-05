"""
MongoDB Client

MongoDB database client for storing OCR results and job data.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
import pymongo

logger = logging.getLogger(__name__)


class MongoDBClient:
    """
    MongoDB client for OCR service.

    Handles connections to MongoDB and provides methods for storing
    and retrieving OCR results, job data, and metadata.
    """

    def __init__(self, connection_url: str, database_name: str = "ocr_results"):
        """
        Initialize MongoDB client.

        Args:
            connection_url: MongoDB connection URL
            database_name: Name of the database to use
        """
        self.connection_url = connection_url
        self.database_name = database_name
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """
        Establish connection to MongoDB.

        Raises:
            ConnectionError: If connection fails
        """
        try:
            logger.info(f"Connecting to MongoDB: {self.database_name}")

            # Create async client
            self._client = AsyncIOMotorClient(
                self.connection_url,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,         # 10 second connect timeout
                socketTimeoutMS=20000,          # 20 second socket timeout
                retryWrites=True,
                maxPoolSize=50
            )

            # Get database reference
            self._database = self._client[self.database_name]

            # Test connection
            await self._client.admin.command('ping')

            # Create indexes
            await self.create_indexes()

            logger.info("MongoDB connection established successfully")

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise ConnectionError(f"MongoDB connection failed: {e}")

    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("MongoDB connection closed")

    async def create_indexes(self) -> None:
        """Create necessary database indexes for optimal performance."""
        if self._database is None:
            return

        try:
            # OCR Results indexes
            ocr_results = self._database.ocr_results
            await ocr_results.create_index([("job_id", 1)], unique=True)
            await ocr_results.create_index([("user_id", 1)])
            await ocr_results.create_index([("created_at", -1)])
            await ocr_results.create_index([("overall_confidence", -1)])
            await ocr_results.create_index([("user_id", 1), ("created_at", -1)])

            # Job Status indexes
            job_status = self._database.job_status
            await job_status.create_index([("job_id", 1)], unique=True)
            await job_status.create_index([("status", 1)])
            await job_status.create_index([("created_at", -1)])
            await job_status.create_index([("user_id", 1), ("created_at", -1)])

            # User Corrections indexes
            user_corrections = self._database.user_corrections
            await user_corrections.create_index([("result_id", 1)])
            await user_corrections.create_index([("user_id", 1)])
            await user_corrections.create_index([("created_at", -1)])

            logger.info("MongoDB indexes created successfully")

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    # OCR Results Operations
    async def store_ocr_result(
        self,
        job_id: str,
        result_data: Dict[str, Any]
    ) -> str:
        """
        Store OCR processing result.

        Args:
            job_id: Associated job identifier
            result_data: OCR result data

        Returns:
            Result document ID
        """
        if self._database is None:
            raise RuntimeError("Database not connected")

        try:
            collection = self._database.ocr_results

            # Prepare document
            document = {
                "job_id": job_id,
                "invoice_id": result_data.get("invoice_id"),
                "user_id": result_data.get("user_id"),
                "message_id": result_data.get("message_id"),
                "original_image_url": result_data.get("original_image_url"),
                "processed_image_url": result_data.get("processed_image_url"),
                "enhanced_image_url": result_data.get("enhanced_image_url"),

                # Raw OCR output from PaddleOCR
                "raw_ocr_result": {
                    "full_text": result_data.get("full_text", ""),
                    "text_blocks": result_data.get("raw_text_regions", []),
                    "processing_time_ms": result_data.get("processing_time", 0) * 1000,
                    "paddle_version": "2.7+",
                    "model_used": "thai"
                },

                # Structured parsed results
                "ocr_results": {
                    "vendor": result_data.get("vendor_field", {"value": None, "confidence": 0.0}),
                    "invoice_number": result_data.get("invoice_number_field", {"value": None, "confidence": 0.0}),
                    "date": result_data.get("date_field", {"value": None, "confidence": 0.0}),
                    "total_amount": result_data.get("total_amount_field", {"value": None, "confidence": 0.0}),
                    "line_items": result_data.get("line_items", [])
                },

                "overall_confidence": result_data.get("confidence_score", 0.0),
                "user_corrections": None,

                "processing_metadata": {
                    "frontend_preprocessed": result_data.get("frontend_preprocessed", False),
                    "backend_preprocessing_job_id": result_data.get("preprocessing_job_id"),
                    "ocr_job_id": job_id,
                    "total_processing_time_ms": result_data.get("total_processing_time", 0) * 1000,
                    "preprocessing_operations": result_data.get("preprocessing_operations", []),
                    "image_quality_improvement": result_data.get("image_quality_improvement", 0.0)
                },

                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }

            # Insert document
            result = await collection.insert_one(document)

            logger.info(f"Stored OCR result for job {job_id}: {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to store OCR result for job {job_id}: {e}")
            raise

    async def get_ocr_result(
        self,
        result_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve OCR result by ID.

        Args:
            result_id: Result identifier

        Returns:
            OCR result data or None if not found
        """
        if self._database is None:
            raise RuntimeError("Database not connected")

        try:
            collection = self._database.ocr_results

            # Convert string ID to ObjectId if necessary
            if len(result_id) == 24:
                query = {"_id": ObjectId(result_id)}
            else:
                query = {"job_id": result_id}

            result = await collection.find_one(query)

            if result:
                # Convert ObjectId to string for JSON serialization
                result["_id"] = str(result["_id"])
                logger.debug(f"Retrieved OCR result: {result_id}")

            return result

        except Exception as e:
            logger.error(f"Failed to retrieve OCR result {result_id}: {e}")
            return None

    async def update_ocr_result(
        self,
        result_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update OCR result.

        Args:
            result_id: Result identifier
            updates: Fields to update

        Returns:
            True if update successful
        """
        if self._database is None:
            raise RuntimeError("Database not connected")

        try:
            collection = self._database.ocr_results

            # Convert string ID to ObjectId if necessary
            if len(result_id) == 24:
                query = {"_id": ObjectId(result_id)}
            else:
                query = {"job_id": result_id}

            # Add updated timestamp
            updates["updated_at"] = datetime.now(timezone.utc)

            result = await collection.update_one(
                query,
                {"$set": updates}
            )

            success = result.modified_count > 0
            if success:
                logger.info(f"Updated OCR result: {result_id}")
            else:
                logger.warning(f"No OCR result found to update: {result_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to update OCR result {result_id}: {e}")
            return False

    # Job Status Operations
    async def store_job_status(
        self,
        job_data: Dict[str, Any]
    ) -> str:
        """
        Store job status information.

        Args:
            job_data: Job status data

        Returns:
            Job document ID
        """
        if self._database is None:
            raise RuntimeError("Database not connected")

        try:
            collection = self._database.job_status

            document = {
                "job_id": job_data.get("job_id"),
                "user_id": job_data.get("user_id"),
                "message_id": job_data.get("message_id"),
                "status": job_data.get("status", "pending"),
                "progress": job_data.get("progress", 0),
                "stage": job_data.get("stage", "initializing"),
                "error_message": job_data.get("error_message"),
                "result_data": job_data.get("result_data"),
                "processing_time": job_data.get("processing_time", 0),
                "webhook_url": job_data.get("webhook_url"),
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }

            result = await collection.insert_one(document)
            logger.info(f"Stored job status for {job_data.get('job_id')}: {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to store job status: {e}")
            raise

    async def update_job_status(
        self,
        job_id: str,
        status_updates: Dict[str, Any]
    ) -> bool:
        """
        Update job status.

        Args:
            job_id: Job identifier
            status_updates: Status fields to update

        Returns:
            True if update successful
        """
        if self._database is None:
            raise RuntimeError("Database not connected")

        try:
            collection = self._database.job_status

            # Add updated timestamp
            status_updates["updated_at"] = datetime.now(timezone.utc)

            result = await collection.update_one(
                {"job_id": job_id},
                {"$set": status_updates},
                upsert=True
            )

            success = result.modified_count > 0 or result.upserted_id is not None
            if success:
                logger.debug(f"Updated job status for {job_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to update job status {job_id}: {e}")
            return False

    async def get_job_status(
        self,
        job_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get job status information.

        Args:
            job_id: Job identifier

        Returns:
            Job status data or None if not found
        """
        if self._database is None:
            raise RuntimeError("Database not connected")

        try:
            collection = self._database.job_status
            result = await collection.find_one({"job_id": job_id})

            if result:
                result["_id"] = str(result["_id"])

            return result

        except Exception as e:
            logger.error(f"Failed to get job status {job_id}: {e}")
            return None

    # User Corrections Operations
    async def store_user_corrections(
        self,
        result_id: str,
        corrections: Dict[str, Any],
        user_id: str
    ) -> str:
        """
        Store user corrections for learning.

        Args:
            result_id: Original OCR result ID
            corrections: User corrections
            user_id: User who made corrections

        Returns:
            Correction document ID
        """
        if self._database is None:
            raise RuntimeError("Database not connected")

        try:
            collection = self._database.user_corrections

            document = {
                "result_id": result_id,
                "user_id": user_id,
                "corrections": corrections,
                "corrected_at": datetime.now(timezone.utc),
                "created_at": datetime.now(timezone.utc)
            }

            result = await collection.insert_one(document)

            # Also update the original OCR result
            await self.update_ocr_result(result_id, {
                "user_corrections": {
                    "corrected_at": document["corrected_at"],
                    "corrected_by": user_id,
                    "corrections": corrections,
                    "user_verified": True
                }
            })

            logger.info(f"Stored user corrections for result {result_id}: {result.inserted_id}")
            return str(result.inserted_id)

        except Exception as e:
            logger.error(f"Failed to store user corrections: {e}")
            raise

    # Query Operations
    async def find_results_by_user(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Find OCR results for a specific user.

        Args:
            user_id: User identifier
            limit: Maximum results to return
            skip: Number of results to skip

        Returns:
            List of OCR results
        """
        if self._database is None:
            raise RuntimeError("Database not connected")

        try:
            collection = self._database.ocr_results
            cursor = collection.find(
                {"user_id": user_id}
            ).sort("created_at", -1).skip(skip).limit(limit)

            results = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                results.append(doc)

            logger.debug(f"Found {len(results)} OCR results for user {user_id}")
            return results

        except Exception as e:
            logger.error(f"Failed to find results by user {user_id}: {e}")
            return []

    async def find_results_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find OCR results within date range.

        Args:
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum results to return

        Returns:
            List of OCR results
        """
        if self._database is None:
            raise RuntimeError("Database not connected")

        try:
            collection = self._database.ocr_results
            cursor = collection.find({
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }).sort("created_at", -1).limit(limit)

            results = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                results.append(doc)

            logger.debug(f"Found {len(results)} OCR results in date range")
            return results

        except Exception as e:
            logger.error(f"Failed to find results by date range: {e}")
            return []

    # Statistics Operations
    async def get_processing_stats(
        self,
        date_range: Optional[tuple] = None
    ) -> Dict[str, Any]:
        """
        Get processing statistics.

        Args:
            date_range: Optional (start_date, end_date) tuple

        Returns:
            Statistics dictionary
        """
        if self._database is None:
            raise RuntimeError("Database not connected")

        try:
            ocr_collection = self._database.ocr_results
            job_collection = self._database.job_status

            # Build date filter
            date_filter = {}
            if date_range:
                start_date, end_date = date_range
                date_filter = {
                    "created_at": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                }

            # Calculate statistics
            total_jobs = await job_collection.count_documents(date_filter)
            completed_jobs = await job_collection.count_documents({
                **date_filter,
                "status": "completed"
            })
            failed_jobs = await job_collection.count_documents({
                **date_filter,
                "status": "failed"
            })

            # OCR-specific stats
            total_results = await ocr_collection.count_documents(date_filter)

            # Average confidence
            pipeline = [
                {"$match": date_filter},
                {"$group": {
                    "_id": None,
                    "avg_confidence": {"$avg": "$overall_confidence"},
                    "max_confidence": {"$max": "$overall_confidence"},
                    "min_confidence": {"$min": "$overall_confidence"}
                }}
            ]

            confidence_stats = await ocr_collection.aggregate(pipeline).to_list(1)
            if confidence_stats:
                avg_confidence = confidence_stats[0].get("avg_confidence", 0.0)
                max_confidence = confidence_stats[0].get("max_confidence", 0.0)
                min_confidence = confidence_stats[0].get("min_confidence", 0.0)
            else:
                avg_confidence = max_confidence = min_confidence = 0.0

            stats = {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0.0,
                "total_ocr_results": total_results,
                "average_confidence": avg_confidence,
                "max_confidence": max_confidence,
                "min_confidence": min_confidence,
                "generated_at": datetime.now(timezone.utc)
            }

            logger.debug(f"Generated processing statistics: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Failed to get processing statistics: {e}")
            return {}

    # Health Check
    async def health_check(self) -> Dict[str, Any]:
        """
        Check database connection health.

        Returns:
            Health status information
        """
        try:
            if not self._client:
                return {
                    "status": "disconnected",
                    "message": "No database connection",
                    "timestamp": datetime.now(timezone.utc)
                }

            # Ping the database
            await self._client.admin.command('ping')

            # Get server info
            server_info = await self._client.server_info()

            # Collection counts
            ocr_count = await self._database.ocr_results.count_documents({})
            job_count = await self._database.job_status.count_documents({})

            return {
                "status": "healthy",
                "database": self.database_name,
                "server_version": server_info.get("version", "unknown"),
                "collections": {
                    "ocr_results": ocr_count,
                    "job_status": job_count
                },
                "timestamp": datetime.now(timezone.utc)
            }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc)
            }

    @property
    def is_connected(self) -> bool:
        """Check if client is connected to database."""
        return self._client is not None and self._database is not None