"""Unit tests for URI parsing service."""

import pytest

from envresolve.exceptions import URIParseError
from envresolve.services.reference import is_secret_uri, parse_secret_uri


def test_parse_akv_uri_simple() -> None:
    """Test parsing simple akv:// URI."""
    result = parse_secret_uri("akv://my-vault/secret-name")
    assert result["scheme"] == "akv"
    assert result["vault"] == "my-vault"
    assert result["secret"] == "secret-name"
    assert result["version"] is None


def test_parse_akv_uri_with_version() -> None:
    """Test parsing akv:// URI with version parameter."""
    result = parse_secret_uri("akv://my-vault/secret-name?version=abc123")
    assert result["scheme"] == "akv"
    assert result["vault"] == "my-vault"
    assert result["secret"] == "secret-name"
    assert result["version"] == "abc123"


def test_parse_uri_with_hyphen_in_vault_name() -> None:
    """Test vault names can contain hyphens."""
    result = parse_secret_uri("akv://my-company-vault/secret")
    assert result["vault"] == "my-company-vault"


def test_parse_uri_with_hyphen_in_secret_name() -> None:
    """Test secret names can contain hyphens."""
    result = parse_secret_uri("akv://vault/my-secret-name")
    assert result["secret"] == "my-secret-name"


def test_parse_uri_invalid_scheme_raises_error() -> None:
    """Test that non-target URI schemes raise URIParseError."""
    with pytest.raises(URIParseError) as exc:
        parse_secret_uri("postgres://localhost/db")
    assert "scheme" in str(exc.value).lower() or "postgres" in str(exc.value)


def test_parse_uri_missing_vault_raises_error() -> None:
    """Test that URI without vault name raises URIParseError."""
    with pytest.raises(URIParseError) as exc:
        parse_secret_uri("akv:///secret-name")
    assert "vault" in str(exc.value).lower()


def test_parse_uri_missing_secret_raises_error() -> None:
    """Test that URI without secret name raises URIParseError."""
    with pytest.raises(URIParseError) as exc:
        parse_secret_uri("akv://my-vault/")
    assert "secret" in str(exc.value).lower()


def test_parse_uri_empty_raises_error() -> None:
    """Test that empty string raises URIParseError."""
    with pytest.raises(URIParseError):
        parse_secret_uri("")


def test_parse_uri_returns_dict() -> None:
    """Test that parse_secret_uri returns a dictionary."""
    result = parse_secret_uri("akv://vault/secret")
    assert isinstance(result, dict)
    assert "scheme" in result
    assert "vault" in result
    assert "secret" in result
    assert "version" in result


def test_is_secret_uri_true_for_akv() -> None:
    """Test is_secret_uri returns True for akv:// URIs."""
    assert is_secret_uri("akv://vault/secret") is True


def test_is_secret_uri_false_for_other_schemes() -> None:
    """Test is_secret_uri returns False for non-secret URIs."""
    assert is_secret_uri("postgres://localhost/db") is False
    assert is_secret_uri("https://example.com") is False
    assert is_secret_uri("just-a-string") is False


def test_is_secret_uri_false_for_empty() -> None:
    """Test is_secret_uri returns False for empty string."""
    assert is_secret_uri("") is False
