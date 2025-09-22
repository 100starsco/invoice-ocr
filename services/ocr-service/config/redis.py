import os
from .types import RedisConfig

def get_redis_config() -> RedisConfig:
    return RedisConfig(
        url=os.getenv('REDIS_URL', 'redis://localhost:6379')
    )