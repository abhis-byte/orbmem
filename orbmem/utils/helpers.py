# utils/helpers.py

import json
import time
from typing import Any, Dict


def now_ts() -> float:
    """
    Returns the current time as a Unix timestamp.
    """
    return time.time()


def safe_json(data: Any) -> str:
    """
    Convert Python dict/list/value → JSON string safely.
    Used for logging or storing structured data.
    """
    try:
        return json.dumps(data, ensure_ascii=False, default=str)
    except Exception:
        return "{}"


def deep_clean_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove None values from dict recursively.
    Useful for preparing clean API responses.
    """
    if not isinstance(data, dict):
        return data

    cleaned = {}
    for k, v in data.items():
        if v is None:
            continue
        if isinstance(v, dict):
            cleaned[k] = deep_clean_dict(v)
        else:
            cleaned[k] = v

    return cleaned


def ensure_str(value: Any) -> str:
    """
    Safely convert value → string.
    Avoids crashes during logging or database operations.
    """
    try:
        return str(value)
    except Exception:
        return "<unprintable>"
