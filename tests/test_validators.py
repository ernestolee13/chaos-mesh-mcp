"""Tests for validators."""

import pytest
from chaos_mesh_mcp.validators import (
    validate_duration,
    validate_percentage,
    validate_memory_size,
    validate_mode,
    validate_direction,
    ValidationError
)


def test_validate_duration():
    """Test duration validation."""
    # Valid
    validate_duration("10ms")
    validate_duration("1s")
    validate_duration("5m")
    validate_duration("2h")

    # Invalid
    with pytest.raises(ValidationError):
        validate_duration("invalid")
    with pytest.raises(ValidationError):
        validate_duration("10")
    with pytest.raises(ValidationError):
        validate_duration("10seconds")


def test_validate_percentage():
    """Test percentage validation."""
    # Valid
    validate_percentage("0")
    validate_percentage("50")
    validate_percentage("100")
    validate_percentage("50.5")

    # Invalid
    with pytest.raises(ValidationError):
        validate_percentage("-1")
    with pytest.raises(ValidationError):
        validate_percentage("101")
    with pytest.raises(ValidationError):
        validate_percentage("abc")


def test_validate_memory_size():
    """Test memory size validation."""
    # Valid
    validate_memory_size("256MB")
    validate_memory_size("1GB")
    validate_memory_size("512KB")

    # Invalid
    with pytest.raises(ValidationError):
        validate_memory_size("256")
    with pytest.raises(ValidationError):
        validate_memory_size("1TB")  # Not supported
    with pytest.raises(ValidationError):
        validate_memory_size("invalid")


def test_validate_mode():
    """Test mode validation."""
    # Valid
    validate_mode("one")
    validate_mode("all")
    validate_mode("fixed")
    validate_mode("fixed-percent")

    # Invalid
    with pytest.raises(ValidationError):
        validate_mode("invalid")


def test_validate_direction():
    """Test direction validation."""
    # Valid
    validate_direction("to")
    validate_direction("from")
    validate_direction("both")

    # Invalid
    with pytest.raises(ValidationError):
        validate_direction("invalid")
