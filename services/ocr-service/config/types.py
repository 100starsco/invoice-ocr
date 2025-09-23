from typing import Optional
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    mongodb_uri: str

@dataclass
class RedisConfig:
    url: str

@dataclass
class OCRConfig:
    language: str
    use_gpu: bool = False
    max_image_size: int = 2048
    confidence_threshold: float = 0.8

@dataclass
class QueueConfig:
    default_queue: str = 'default'
    preprocessing_queue: str = 'preprocessing'
    ocr_queue: str = 'ocr'
    retry_attempts: int = 3
    job_timeout: int = 300

@dataclass
class MonitoringConfig:
    rq_dashboard_port: int
    rq_dashboard_redis_url: str
    log_level: str = 'INFO'

@dataclass
class EnvironmentConfig:
    env: str
    node_env: str
    port: Optional[int] = 8001
    debug: bool = False
    is_production: bool = False
    is_development: bool = False

@dataclass
class OCRServiceConfig:
    environment: EnvironmentConfig
    database: DatabaseConfig
    redis: RedisConfig
    ocr: OCRConfig
    queue: QueueConfig
    monitoring: MonitoringConfig