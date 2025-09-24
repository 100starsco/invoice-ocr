"""
RQ Dashboard Startup Script

Script to start the RQ dashboard for queue monitoring.
"""

import sys
import logging
import subprocess
import time
import redis
from config import config


def setup_logging():
    """Setup logging for dashboard."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def test_redis_connection(redis_url: str, max_retries: int = 5) -> bool:
    """
    Test Redis connection before starting dashboard.

    Args:
        redis_url: Redis connection URL
        max_retries: Maximum number of connection attempts

    Returns:
        True if connection successful, False otherwise
    """
    logger = logging.getLogger(__name__)

    for attempt in range(1, max_retries + 1):
        try:
            # Parse Redis URL and create connection
            redis_client = redis.from_url(redis_url)
            redis_client.ping()
            logger.info(f"Redis connection successful on attempt {attempt}")
            redis_client.close()
            return True
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(2)  # Wait 2 seconds before retry
            continue
        except Exception as e:
            logger.error(f"Unexpected error testing Redis connection: {e}")
            return False

    logger.error(f"Failed to connect to Redis after {max_retries} attempts")
    return False


def start_dashboard():
    """
    Start RQ dashboard with proper configuration.
    """
    logger = logging.getLogger(__name__)

    try:
        # Use configuration from config module
        port = config.monitoring.rq_dashboard_port
        redis_url = config.monitoring.rq_dashboard_redis_url

        logger.info(f"Starting RQ dashboard on port {port}")
        logger.info(f"Redis URL: {redis_url}")

        # Test Redis connection first
        if not test_redis_connection(redis_url):
            logger.error("Cannot start dashboard: Redis connection failed")
            sys.exit(1)

        # Start RQ dashboard process
        logger.info("Redis connection verified, starting dashboard...")

        dashboard_cmd = [
            "rq-dashboard",
            "--redis-url", redis_url,
            "--port", str(port),
            "--interval", "5000",  # 5 second refresh interval
            "--verbose"
        ]

        logger.info(f"Executing command: {' '.join(dashboard_cmd)}")

        # Run dashboard in foreground
        result = subprocess.run(dashboard_cmd, check=True)

        if result.returncode == 0:
            logger.info("RQ Dashboard started successfully")
        else:
            logger.error(f"Dashboard exited with code {result.returncode}")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start RQ dashboard subprocess: {e}")
        logger.error(f"Command that failed: {e.cmd}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error("rq-dashboard command not found. Make sure rq-dashboard is installed.")
        logger.error("Try: pip install rq-dashboard")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Dashboard shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error starting dashboard: {e}")
        sys.exit(1)


def main():
    """
    Main function.

    Sets up logging and starts the RQ dashboard with proper error handling.
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=== RQ Dashboard Startup ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Config environment: {config.environment.env}")

    try:
        start_dashboard()
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()