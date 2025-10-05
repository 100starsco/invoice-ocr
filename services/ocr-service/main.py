"""
Invoice OCR Service

FastAPI application for Thai invoice OCR processing with PaddleOCR,
Redis queue management, and MongoDB result storage.
"""

import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.dependencies import get_database, get_redis_client
from app.database import MongoDBClient, RedisClient
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("ocr_service.log") if config.environment.node_env == "production" else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global clients (will be initialized in lifespan)
mongodb_client: MongoDBClient = None
redis_client: RedisClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for database connections
    and resource initialization.
    """
    # Startup
    logger.info("Starting OCR Service...")

    try:
        # Initialize database connections
        global mongodb_client, redis_client

        # Initialize MongoDB client
        from app.database.mongodb import MongoDBClient
        mongodb_client = MongoDBClient(
            connection_url=config.database.mongodb_uri,
            database_name="ocr_results"
        )
        await mongodb_client.connect()
        logger.info("MongoDB connection established")

        # Initialize Redis client
        from app.database.redis_client import get_redis_connection
        redis_conn = get_redis_connection()
        redis_conn.ping()  # Test connection
        logger.info("Redis connection established")

        # Initialize OCR engine globally (optional - engines are created per job)
        from app.core.ocr_engine import OCREngine
        test_ocr_engine = OCREngine(language=config.ocr.language)
        test_ocr_engine.initialize()
        test_ocr_engine.cleanup()  # Just test initialization
        logger.info("OCR engine initialization test passed")

        logger.info("OCR Service started successfully")

    except Exception as e:
        logger.error(f"Failed to start OCR Service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down OCR Service...")

    try:
        # Cleanup database connections
        if mongodb_client:
            await mongodb_client.disconnect()
            logger.info("MongoDB connection closed")

        logger.info("Redis connection closed (no explicit cleanup needed)")

        logger.info("OCR Service shutdown completed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="Invoice OCR Service",
    description="FastAPI service for Thai invoice OCR processing using PaddleOCR",
    version="1.0.0",
    docs_url="/docs" if config.environment.is_development else None,
    redoc_url="/redoc" if config.environment.is_development else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if config.environment.is_development else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if config.environment.is_development else ["localhost", "127.0.0.1"]
)


@app.get("/", tags=["Root"])
async def read_root() -> Dict[str, Any]:
    """
    Root endpoint with service information.

    Returns:
        Service information and status
    """
    return {
        "message": "Invoice OCR Service",
        "version": "1.0.0",
        "description": "FastAPI OCR service for Thai invoice processing",
        "environment": config.environment.node_env,
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "docs": "/docs" if config.environment.is_development else "disabled",
        }
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        Service health status and component information
    """
    health_status = {
        "status": "healthy",
        "service": "ocr-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": config.environment.node_env,
        "components": {
            "database": "unknown",
            "redis": "unknown",
            "ocr_engine": "unknown"
        }
    }

    # Check component health
    try:
        # Check MongoDB connection
        if mongodb_client and mongodb_client.is_connected:
            db_health = await mongodb_client.health_check()
            health_status["components"]["database"] = db_health["status"]
            if db_health["status"] != "healthy":
                health_status["status"] = "degraded"
        else:
            health_status["components"]["database"] = "disconnected"
            health_status["status"] = "degraded"

        # Check Redis connection
        if redis_client and hasattr(redis_client, 'is_connected') and redis_client.is_connected:
            # Test Redis with a ping
            try:
                from .app.database.redis_client import get_redis_connection
                redis_conn = get_redis_connection()
                redis_conn.ping()
                health_status["components"]["redis"] = "healthy"
            except Exception:
                health_status["components"]["redis"] = "unhealthy"
                health_status["status"] = "degraded"
        else:
            health_status["components"]["redis"] = "disconnected"
            health_status["status"] = "degraded"

        # Check OCR engine (test initialization)
        try:
            from app.core.ocr_engine import OCREngine
            # Use configured language for health check
            test_engine = OCREngine(language=config.ocr.language, use_gpu=False)
            test_engine.initialize()
            if test_engine.is_initialized():
                health_status["components"]["ocr_engine"] = "healthy"
            else:
                health_status["components"]["ocr_engine"] = "unhealthy"
                health_status["status"] = "degraded"
            test_engine.cleanup()
        except Exception as e:
            logger.warning(f"OCR engine health check failed: {e}")
            health_status["components"]["ocr_engine"] = "unhealthy"
            health_status["status"] = "degraded"

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)

    return health_status


@app.get("/metrics", tags=["Monitoring"])
async def get_metrics() -> Dict[str, Any]:
    """
    Service metrics endpoint.

    Returns:
        Performance and usage metrics
    """
    import psutil
    import time
    from datetime import datetime, timezone

    try:
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "ocr-service",
            "version": "1.0.0"
        }

        # System metrics
        process = psutil.Process()
        metrics["system"] = {
            "memory_usage_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "memory_percent": round(process.memory_percent(), 2),
            "cpu_percent": round(process.cpu_percent(), 2),
            "uptime_seconds": round(time.time() - process.create_time()),
            "threads": process.num_threads()
        }

        # Database metrics
        if mongodb_client and mongodb_client.is_connected:
            try:
                db_stats = await mongodb_client.get_processing_stats()
                metrics["database"] = {
                    "total_jobs": db_stats.get("total_jobs", 0),
                    "completed_jobs": db_stats.get("completed_jobs", 0),
                    "failed_jobs": db_stats.get("failed_jobs", 0),
                    "success_rate": db_stats.get("success_rate", 0.0),
                    "total_ocr_results": db_stats.get("total_ocr_results", 0),
                    "average_confidence": db_stats.get("average_confidence", 0.0)
                }
            except Exception as e:
                logger.warning(f"Failed to get database metrics: {e}")
                metrics["database"] = {"status": "error", "error": str(e)}
        else:
            metrics["database"] = {"status": "disconnected"}

        # Queue metrics (if Redis is available)
        if redis_client:
            try:
                from .app.database.redis_client import get_redis_connection
                from rq import Queue

                redis_conn = get_redis_connection()
                ocr_queue = Queue('ocr', connection=redis_conn)
                ocr_extraction_queue = Queue('ocr_extraction', connection=redis_conn)

                metrics["queues"] = {
                    "ocr_queue_length": len(ocr_queue),
                    "ocr_extraction_queue_length": len(ocr_extraction_queue),
                    "total_queued_jobs": len(ocr_queue) + len(ocr_extraction_queue)
                }
            except Exception as e:
                logger.warning(f"Failed to get queue metrics: {e}")
                metrics["queues"] = {"status": "error", "error": str(e)}
        else:
            metrics["queues"] = {"status": "disconnected"}

        return metrics

    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "metrics_error"
        }


# Add API routes
from app.api.jobs import router as jobs_router
from app.api.images import router as images_router

app.include_router(jobs_router, prefix="/api/v1", tags=["Jobs"])
app.include_router(images_router, tags=["Images"])


def create_app() -> FastAPI:
    """
    Application factory function.

    Returns:
        Configured FastAPI application
    """
    return app


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.environment.port or 8001,
        reload=config.environment.is_development,
        log_level="info",
        access_log=True
    )