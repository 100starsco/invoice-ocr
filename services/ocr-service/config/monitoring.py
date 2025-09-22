import os
from .types import MonitoringConfig

def get_monitoring_config() -> MonitoringConfig:
    return MonitoringConfig(
        rq_dashboard_port=int(os.getenv('RQ_DASHBOARD_PORT', '9181')),
        rq_dashboard_redis_url=os.getenv('RQ_DASHBOARD_REDIS_URL', 'redis://localhost:6379'),
        log_level=os.getenv('LOG_LEVEL', 'INFO')
    )