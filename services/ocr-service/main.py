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

        # TODO: Initialize MongoDB client
        # mongodb_client = MongoDBClient(config.database.mongodb_uri)
        # await mongodb_client.connect()

        # TODO: Initialize Redis client
        # redis_client = RedisClient(config.redis.redis_url)
        # await redis_client.connect()

        # TODO: Initialize OCR engine
        # ocr_engine = OCREngine(language=config.ocr.language)
        # ocr_engine.initialize()

        logger.info("OCR Service started successfully")

    except Exception as e:
        logger.error(f"Failed to start OCR Service: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down OCR Service...")

    try:
        # TODO: Cleanup database connections
        # if mongodb_client:
        #     await mongodb_client.disconnect()
        # if redis_client:
        #     await redis_client.disconnect()

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
            "database": "unknown",  # TODO: Check MongoDB connection
            "redis": "unknown",     # TODO: Check Redis connection
            "ocr_engine": "unknown" # TODO: Check OCR engine status
        }
    }

    # TODO: Implement actual health checks
    # try:
    #     if mongodb_client and mongodb_client.is_connected:
    #         health_status["components"]["database"] = "healthy"
    #     if redis_client and redis_client.is_connected:
    #         health_status["components"]["redis"] = "healthy"
    # except Exception as e:
    #     logger.error(f"Health check failed: {e}")
    #     health_status["status"] = "degraded"

    return health_status


@app.get("/metrics", tags=["Monitoring"])
async def get_metrics() -> Dict[str, Any]:
    """
    Service metrics endpoint.

    Returns:
        Performance and usage metrics
    """
    # TODO: Implement metrics collection
    return {
        "jobs_processed": 0,
        "avg_processing_time": 0.0,
        "active_workers": 0,
        "queue_length": 0,
        "error_rate": 0.0,
        "uptime": 0,
        "memory_usage": 0,
        "cpu_usage": 0.0
    }


# TODO: Add API routes
# app.include_router(ocr_router, prefix="/api/v1/ocr", tags=["OCR"])
# app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["Jobs"])


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