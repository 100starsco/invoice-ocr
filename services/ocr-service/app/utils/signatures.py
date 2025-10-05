"""
Webhook Signature Utilities

Provides HMAC-SHA256 signature generation for webhook security.
"""

import hashlib
import hmac
import json
import os
from typing import Dict, Any

# Get webhook secret from environment
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

def generate_webhook_signature(payload: Dict[str, Any]) -> str:
    """
    Generate HMAC-SHA256 signature for webhook payload.

    Args:
        payload: Webhook payload dictionary

    Returns:
        Hex-encoded signature string with sha256= prefix
    """
    if not WEBHOOK_SECRET:
        raise ValueError("WEBHOOK_SECRET not configured")

    # Convert payload to JSON string (deterministic sorting for consistency)
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))

    # Generate HMAC-SHA256 signature
    signature = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        payload_json.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    # Return with sha256= prefix (standard webhook format)
    return f"sha256={signature}"

def verify_webhook_signature(
    payload: Dict[str, Any],
    signature_header: str
) -> bool:
    """
    Verify webhook signature.

    Args:
        payload: Webhook payload dictionary
        signature_header: Signature from X-Webhook-Signature header

    Returns:
        True if signature is valid, False otherwise
    """
    if not WEBHOOK_SECRET:
        return False

    try:
        # Generate expected signature
        expected_signature = generate_webhook_signature(payload)

        # Compare signatures (using hmac.compare_digest for timing attack protection)
        return hmac.compare_digest(expected_signature, signature_header)

    except Exception:
        return False

def get_signature_header() -> Dict[str, str]:
    """
    Get headers dictionary with webhook signature.

    Returns:
        Dictionary with X-Webhook-Signature header
    """
    return {"X-Webhook-Signature": "sha256=placeholder"}  # Placeholder for actual signature