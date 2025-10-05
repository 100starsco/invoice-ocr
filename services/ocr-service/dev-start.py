#!/usr/bin/env python3
"""
Development startup script for OCR Service

This script starts the OCR service in development mode with enhanced logging
and debugging features for testing the LINE chat integration flow.
"""

import os
import sys
import asyncio
import logging
import signal
import subprocess
from pathlib import Path
from datetime import datetime

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Load development environment
from dotenv import load_dotenv

# Load development environment variables
env_file = Path(__file__).parent / '.env.dev'
if env_file.exists():
    load_dotenv(env_file)
    print(f"✓ Loaded development environment from {env_file}")
else:
    print(f"⚠ Development environment file not found: {env_file}")
    print("Using default configuration...")

# Configure enhanced logging for development
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('dev-ocr-service.log', mode='w')  # Overwrite log file on each start
    ]
)

logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if required services are available."""
    print("\n🔍 Checking dependencies...")

    # Check Redis connection
    try:
        import redis
        redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        redis_client.ping()
        print("✓ Redis connection: OK")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("   Please start Redis server: redis-server")
        return False

    # Check MongoDB connection (optional for basic testing)
    try:
        import pymongo
        mongo_client = pymongo.MongoClient(os.getenv('MONGODB_URI', 'mongodb://localhost:27017/ocr_results'))
        mongo_client.server_info()
        print("✓ MongoDB connection: OK")
    except Exception as e:
        print(f"⚠ MongoDB connection failed: {e}")
        print("   MongoDB is optional for basic OCR testing")

    # Check if image storage directory exists
    storage_path = Path(os.getenv('IMAGE_STORAGE_PATH', '/tmp/ocr_images'))
    storage_path.mkdir(parents=True, exist_ok=True)
    print(f"✓ Image storage directory: {storage_path}")

    return True


def start_rq_worker():
    """Start RQ worker in background for job processing."""
    try:
        print("\n🔧 Starting RQ worker...")
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        worker_process = subprocess.Popen([
            'rq', 'worker',
            '--with-scheduler',
            '--url', redis_url,  # Explicitly pass Redis URL
            'ocr',  # Default queue
            'preprocessing',  # Preprocessing queue
            'ocr_extraction',  # OCR extraction queue
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        print(f"✓ RQ worker started (PID: {worker_process.pid})")
        return worker_process
    except Exception as e:
        print(f"❌ Failed to start RQ worker: {e}")
        return None


async def start_fastapi_server():
    """Start FastAPI server with development configuration."""
    print("\n🚀 Starting OCR Service FastAPI server...")
    print(f"   Environment: {os.getenv('NODE_ENV', 'development')}")
    print(f"   Port: {os.getenv('PORT', 8001)}")
    print(f"   Redis URL: {os.getenv('REDIS_URL', 'redis://localhost:6379')}")
    print(f"   Image Storage: {os.getenv('IMAGE_STORAGE_PATH', '/tmp/ocr_images')}")
    print()

    import uvicorn
    from main import app

    # Enhanced development configuration
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=int(os.getenv('PORT', 8001)),
        reload=True,
        reload_dirs=['app'],
        log_level="debug",
        access_log=True,
        use_colors=True,
        loop="asyncio"
    )

    server = uvicorn.Server(config)
    await server.serve()


def print_startup_info():
    """Print helpful startup information for development."""
    print("\n" + "="*60)
    print("🔥 OCR SERVICE DEVELOPMENT MODE")
    print("="*60)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 FastAPI Server: http://localhost:{os.getenv('PORT', 8001)}")
    print(f"📖 API Documentation: http://localhost:{os.getenv('PORT', 8001)}/docs")
    print(f"📊 RQ Dashboard: http://localhost:{os.getenv('RQ_DASHBOARD_PORT', 9181)}")
    print()
    print("📋 Available Endpoints:")
    print("  • POST /api/v1/jobs/process-invoice - Submit OCR job")
    print("  • GET  /api/v1/jobs/{job_id}/status - Check job status")
    print("  • GET  /health - Health check")
    print("  • GET  /images/{filename} - Serve processed images")
    print("  • GET  /images/stats - Storage statistics")
    print()
    print("🧪 Testing Flow:")
    print("  1. Send image from LINE chat")
    print("  2. Check logs for processing stages")
    print("  3. View results in webhook logs")
    print("  4. Monitor queues in RQ Dashboard")
    print()
    print("📝 Log Files:")
    print("  • dev-ocr-service.log - Application logs")
    print("  • Access logs - Console output")
    print()
    print("🛑 To stop: Press Ctrl+C")
    print("="*60)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n📡 Received signal {signum}, shutting down gracefully...")
    sys.exit(0)


async def main():
    """Main development startup function."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print_startup_info()

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency checks failed. Please fix the issues above.")
        return 1

    # Start RQ worker in background
    worker_process = start_rq_worker()

    try:
        # Start FastAPI server (this will block)
        await start_fastapi_server()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        # Clean up worker process
        if worker_process:
            print("🔧 Stopping RQ worker...")
            worker_process.terminate()
            worker_process.wait()
            print("✓ RQ worker stopped")

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Failed to start development server: {e}")
        sys.exit(1)