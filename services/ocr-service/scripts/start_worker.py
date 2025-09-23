"""
RQ Worker Startup Script

Script to start RQ workers for background job processing.
"""

import sys
import logging
from rq import Worker, Queue, Connection
import redis

from config import config


def setup_logging():
    """Setup logging for worker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("worker.log")
        ]
    )


def start_worker(queue_names=None):
    """
    Start RQ worker.

    Args:
        queue_names: List of queue names to listen to
    """
    if queue_names is None:
        queue_names = [
            config.queue.default_queue,
            config.queue.preprocessing_queue,
            config.queue.ocr_queue
        ]

    # TODO: Implement worker startup
    # redis_conn = redis.from_url(config.redis.url)
    # queues = [Queue(name, connection=redis_conn) for name in queue_names]
    # worker = Worker(queues, connection=redis_conn)
    # worker.work()

    print(f"Starting worker for queues: {queue_names}")
    print("Worker startup logic not implemented yet")


def main():
    """Main function."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting RQ worker...")

    try:
        start_worker()
    except KeyboardInterrupt:
        logger.info("Worker shutdown requested")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()