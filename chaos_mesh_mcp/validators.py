"""Parameter validation utilities for Chaos Mesh."""

import re
from typing import Dict, List


class ValidationError(Exception):
    """Validation error for Chaos Mesh parameters."""
    pass


def validate_duration(duration: str) -> None:
    """Validate duration format (e.g., '10ms', '1s', '2m', '1h').

    Args:
        duration: Duration string

    Raises:
        ValidationError: If format is invalid
    """
    if not re.match(r'^\d+(ms|s|m|h)$', duration):
        raise ValidationError(
            f"Invalid duration format: '{duration}'. "
            "Expected format: <number><unit> (e.g., '10ms', '1s', '2m', '1h')"
        )


def validate_percentage(value: str) -> None:
    """Validate percentage value (0-100).

    Args:
        value: Percentage as string

    Raises:
        ValidationError: If not in valid range
    """
    try:
        num = float(value)
        if not 0 <= num <= 100:
            raise ValidationError(f"Percentage must be 0-100, got {value}")
    except ValueError:
        raise ValidationError(f"Invalid percentage value: {value}")


def validate_memory_size(size: str) -> None:
    """Validate memory size format (e.g., '256MB', '1GB').

    Args:
        size: Memory size string

    Raises:
        ValidationError: If format is invalid
    """
    if not re.match(r'^\d+(B|KB|MB|GB|TB)$', size, re.IGNORECASE):
        raise ValidationError(
            f"Invalid memory size format: '{size}'. "
            "Expected format: <number><unit> (e.g., '256MB', '1GB')"
        )


def validate_mode(mode: str) -> None:
    """Validate Chaos Mesh mode.

    Args:
        mode: Mode string

    Raises:
        ValidationError: If mode is invalid
    """
    valid_modes = ["one", "all", "fixed", "fixed-percent", "random-max-percent"]
    if mode not in valid_modes:
        raise ValidationError(
            f"Invalid mode: '{mode}'. "
            f"Valid modes: {', '.join(valid_modes)}"
        )


def validate_direction(direction: str) -> None:
    """Validate network direction.

    Args:
        direction: Direction string

    Raises:
        ValidationError: If direction is invalid
    """
    valid_directions = ["to", "from", "both"]
    if direction not in valid_directions:
        raise ValidationError(
            f"Invalid direction: '{direction}'. "
            f"Valid directions: {', '.join(valid_directions)}"
        )


def validate_bandwidth(rate: str) -> None:
    """Validate bandwidth format (e.g., '1mbit', '100kbit').

    Args:
        rate: Bandwidth rate string

    Raises:
        ValidationError: If format is invalid
    """
    if not re.match(r'^\d+(bit|kbit|mbit|gbit|bps|kbps|mbps|gbps)$', rate, re.IGNORECASE):
        raise ValidationError(
            f"Invalid bandwidth format: '{rate}'. "
            "Expected format: <number><unit> (e.g., '1mbit', '100kbps')"
        )


def validate_labels(labels: Dict[str, str]) -> None:
    """Validate Kubernetes label selectors.

    Args:
        labels: Label selector dictionary

    Raises:
        ValidationError: If labels are invalid
    """
    if not labels:
        raise ValidationError("Label selectors cannot be empty")

    for key, value in labels.items():
        if not re.match(r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$', key):
            raise ValidationError(f"Invalid label key: '{key}'")
        if not isinstance(value, str):
            raise ValidationError(f"Label value must be string, got {type(value)}")
