import os
from .types import DatabaseConfig

def get_database_config() -> DatabaseConfig:
    return DatabaseConfig(
        mongodb_uri=os.getenv('MONGODB_URI', 'mongodb://localhost:27017/ocr_results')
    )