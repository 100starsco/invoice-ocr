import os
from dotenv import load_dotenv
from .types import EnvironmentConfig

# Load environment variables from .env file
load_dotenv()

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