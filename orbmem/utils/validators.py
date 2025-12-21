# utils/validators.py

import re
from typing import Any, Dict


class ValidationError(Exception):
    """Custom validation error."""
    pass


def validate_non_empty(value: Any, field_name: str = "value"):
    """Ensure a value is not empty or None."""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        raise ValidationError(f"{field_name} cannot be empty.")
    return value


def validate_dict(value: Any, field_name: str = "value"):
    """Ensure the input is a dictionary."""
    if not isinstance(value, dict):
        raise ValidationError(f"{field_name} must be a dictionary.")
    return value


def validate_key_in_dict(data: Dict, key: str):
    """Ensure a key exists in a dictionary."""
    if key not in data:
        raise ValidationError(f"Missing required key: '{key}'")
    return data[key]


def validate_api_key(key: str):
    """Simple API key format validator."""
    validate_non_empty(key, "API key")

    # Example: basic 32-char hex key (you can change this pattern)
    pattern = r"^[A-Fa-f0-9]{32}$"

    if not re.match(pattern, key):
        raise ValidationError("Invalid API key format.")

    return key


def validate_memory_id(mem_id: str):
    """Ensure memory ID follows a sane format."""
    validate_non_empty(mem_id, "Memory ID")

    if not re.match(r"^[A-Za-z0-9_\-]+$", mem_id):
        raise ValidationError("Memory ID contains invalid characters.")

    return mem_id
