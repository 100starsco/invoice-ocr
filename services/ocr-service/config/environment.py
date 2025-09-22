import os
from .types import EnvironmentConfig

def get_environment_config() -> EnvironmentConfig:
    env = os.getenv('ENV', 'development')

    return EnvironmentConfig(
        env=env,
        debug=os.getenv('DEBUG', 'false').lower() == 'true',
        is_production=env == 'production',
        is_development=env == 'development'
    )