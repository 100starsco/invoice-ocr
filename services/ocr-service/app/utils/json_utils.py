"""
JSON Utilities

Helper functions for JSON serialization and data type conversion.
"""

import numpy as np
from typing import Any, Dict, List, Union
import json
from datetime import datetime, date
from decimal import Decimal


def convert_to_json_serializable(obj: Any) -> Any:
    """
    Convert numpy and other non-serializable types to JSON serializable formats.

    Args:
        obj: Object to convert (can be nested dict/list)

    Returns:
        JSON serializable version of the object
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, bytes):
        return obj.decode('utf-8', errors='ignore')
    elif isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Handle custom objects
        return convert_to_json_serializable(obj.__dict__)
    else:
        return obj


def safe_json_dumps(data: Any, **kwargs) -> str:
    """
    Safely serialize data to JSON string, handling numpy types.

    Args:
        data: Data to serialize
        **kwargs: Additional arguments for json.dumps

    Returns:
        JSON string
    """
    # Convert to JSON serializable format first
    serializable_data = convert_to_json_serializable(data)

    # Use default handler for any remaining non-serializable types
    def default_handler(obj):
        if hasattr(obj, 'tolist'):
            return obj.tolist()
        elif hasattr(obj, '__str__'):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    return json.dumps(serializable_data, default=default_handler, **kwargs)


def prepare_webhook_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare webhook payload by converting all values to JSON serializable types.

    Args:
        payload: Webhook payload dictionary

    Returns:
        JSON serializable payload
    """
    return convert_to_json_serializable(payload)