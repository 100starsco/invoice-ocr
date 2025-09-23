import os
from .types import EnvironmentConfig

def get_environment_config() -> EnvironmentConfig:
    env = os.getenv('ENV', 'development')
    node_env = os.getenv('NODE_ENV', env)
    port = int(os.getenv('PORT', '8001'))

    return EnvironmentConfig(
        env=env,
        node_env=node_env,
        port=port,
        debug=os.getenv('DEBUG', 'false').lower() == 'true',
        is_production=env == 'production',
        is_development=env == 'development'
    )