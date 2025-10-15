"""Unit tests for exception classes."""

from envresolve.exceptions import (
    CircularReferenceError,
    EnvResolveError,
    ProviderRegistrationError,
    SecretResolutionError,
    URIParseError,
    VariableNotFoundError,
)


def test_env_resolve_error_exists() -> None:
    """Test that EnvResolveError base exception exists."""
    exc = EnvResolveError("test error")
    assert str(exc) == "test error"
    assert isinstance(exc, Exception)


def test_variable_not_found_error_exists() -> None:
    """Test that VariableNotFoundError exists."""
    exc = VariableNotFoundError("VAR")
    assert "VAR" in str(exc)
    assert isinstance(exc, EnvResolveError)


def test_circular_reference_error_exists() -> None:
    """Test that CircularReferenceError exists."""
    exc = CircularReferenceError("VAR", ["A", "B", "A"])
    assert isinstance(exc, EnvResolveError)


def test_uri_parse_error_exists() -> None:
    """Test that URIParseError exception exists."""
    exc = URIParseError("Invalid URI format")
    assert str(exc) == "Invalid URI format"
    assert isinstance(exc, EnvResolveError)


def test_uri_parse_error_with_uri() -> None:
    """Test URIParseError stores the problematic URI."""
    exc = URIParseError("Bad format", uri="akv://vault/")
    assert exc.uri == "akv://vault/"
    assert "akv://vault/" in str(exc) or "Bad format" in str(exc)


def test_secret_resolution_error_exists() -> None:
    """Test that SecretResolutionError exception exists."""
    original = KeyError("not found")
    exc = SecretResolutionError(
        "Failed to resolve", uri="akv://vault/secret", original_error=original
    )
    assert exc.uri == "akv://vault/secret"
    assert exc.original_error is original
    assert isinstance(exc, EnvResolveError)


def test_secret_resolution_error_message_includes_uri() -> None:
    """Test SecretResolutionError message includes URI."""
    exc = SecretResolutionError(
        "Failed", uri="akv://vault/secret", original_error=KeyError()
    )
    assert "akv://vault/secret" in str(exc)


def test_provider_registration_error_exists() -> None:
    """Test that ProviderRegistrationError exists and inherits from EnvResolveError."""
    exc = ProviderRegistrationError("Failed to register provider")
    assert str(exc) == "Failed to register provider"
    assert isinstance(exc, EnvResolveError)
