"""Unit tests for SecretResolver."""

import os
from unittest.mock import MagicMock

import pytest

from envresolve.application.resolver import SecretResolver
from envresolve.exceptions import CircularReferenceError
from envresolve.models import ParsedURI


class MockProvider:
    """Mock provider for testing."""

    def __init__(self, secret_map: dict[str, str]) -> None:
        """Initialize with a mapping of secrets."""
        self.secret_map = secret_map
        self.resolve_calls: list[ParsedURI] = []

    def resolve(self, parsed_uri: ParsedURI) -> str:
        """Resolve a secret from the mock storage."""
        self.resolve_calls.append(parsed_uri)
        secret_name = parsed_uri["secret"]
        return self.secret_map.get(secret_name, f"mock-value-{secret_name}")


def test_resolver_single_uri_resolution() -> None:
    """Test simple single-level URI resolution."""
    provider = MockProvider({"my-secret": "secret-value"})
    resolver = SecretResolver({"akv": provider})

    result = resolver.resolve("akv://vault/my-secret")

    assert result == "secret-value"
    assert len(provider.resolve_calls) == 1


def test_resolver_plain_string_passthrough() -> None:
    """Test that plain strings pass through without resolution."""
    provider = MockProvider({})
    resolver = SecretResolver({"akv": provider})

    result = resolver.resolve("just-a-plain-string")

    assert result == "just-a-plain-string"
    assert len(provider.resolve_calls) == 0


def test_resolver_uri_to_uri_resolution() -> None:
    """Test URI that resolves to another URI."""
    provider = MockProvider(
        {
            "indirect": "akv://vault/actual",
            "actual": "final-value",
        }
    )
    resolver = SecretResolver({"akv": provider})

    result = resolver.resolve("akv://vault/indirect")

    assert result == "final-value"
    expected_call_count = 2
    assert len(provider.resolve_calls) == expected_call_count
    assert provider.resolve_calls[0]["secret"] == "indirect"  # noqa: S105
    assert provider.resolve_calls[1]["secret"] == "actual"  # noqa: S105


def test_resolver_three_level_chain() -> None:
    """Test three levels of URI resolution."""
    provider = MockProvider(
        {
            "level1": "akv://vault/level2",
            "level2": "akv://vault/level3",
            "level3": "final-secret",
        }
    )
    resolver = SecretResolver({"akv": provider})

    result = resolver.resolve("akv://vault/level1")

    assert result == "final-secret"
    expected_call_count = 3
    assert len(provider.resolve_calls) == expected_call_count


def test_resolver_variable_expansion_in_uri() -> None:
    """Test variable expansion before URI resolution."""
    provider = MockProvider({"my-secret": "secret-value"})
    resolver = SecretResolver({"akv": provider})
    env = {"SECRET_NAME": "my-secret"}

    result = resolver.resolve("akv://vault/${SECRET_NAME}", env)

    assert result == "secret-value"
    assert provider.resolve_calls[0]["secret"] == "my-secret"  # noqa: S105


def test_resolver_variable_expansion_in_resolved_value() -> None:
    """Test variable expansion in resolved URI."""
    provider = MockProvider(
        {
            "indirect": "akv://vault/${FINAL_KEY}",
            "actual": "final-value",
        }
    )
    resolver = SecretResolver({"akv": provider})
    env = {"FINAL_KEY": "actual"}

    result = resolver.resolve("akv://vault/indirect", env)

    assert result == "final-value"
    expected_call_count = 2
    assert len(provider.resolve_calls) == expected_call_count


def test_resolver_circular_reference_detection() -> None:
    """Test that circular URI references are detected."""
    provider = MockProvider(
        {
            "secret1": "akv://vault/secret2",
            "secret2": "akv://vault/secret1",  # Circular!
        }
    )
    resolver = SecretResolver({"akv": provider})

    with pytest.raises(CircularReferenceError) as exc:
        resolver.resolve("akv://vault/secret1")

    assert "secret1" in exc.value.variable_name or "secret1" in str(exc.value.chain)


def test_resolver_circular_reference_with_self_loop() -> None:
    """Test detection of self-referencing URI.

    Note: A URI that resolves to itself (akv://vault/x -> akv://vault/x)
    will be caught by the 'no change' check, not the circular reference check.
    But if it resolves to a different form that eventually comes back,
    it should be caught.
    """
    provider = MockProvider(
        {
            "self-ref": "akv://vault/intermediate",
            "intermediate": "akv://vault/self-ref",  # Goes back to self-ref
        }
    )
    resolver = SecretResolver({"akv": provider})

    with pytest.raises(CircularReferenceError) as exc:
        resolver.resolve("akv://vault/self-ref")

    assert "self-ref" in str(exc.value) or "intermediate" in str(exc.value)


def test_resolver_idempotent_with_plain_result() -> None:
    """Test that resolution stops when result is not a URI."""
    provider = MockProvider({"my-secret": "plain-text-value"})
    resolver = SecretResolver({"akv": provider})

    result = resolver.resolve("akv://vault/my-secret")

    assert result == "plain-text-value"
    # Should only resolve once since result is not a URI
    assert len(provider.resolve_calls) == 1


def test_resolver_stops_when_value_stabilizes() -> None:
    """Test that resolution stops when value no longer changes."""
    # Edge case: provider returns the same URI it received
    # (shouldn't happen in practice, but tests idempotency)
    call_count = 0

    def stable_resolver(_parsed_uri: ParsedURI) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return "akv://vault/stable"
        # Second call returns a non-URI value
        return "stable-value"

    provider = MagicMock()
    provider.resolve = stable_resolver
    resolver = SecretResolver({"akv": provider})

    result = resolver.resolve("akv://vault/start")

    assert result == "stable-value"
    expected_call_count = 2
    assert call_count == expected_call_count


def test_resolver_mixed_expansion_and_resolution() -> None:
    """Test complex case with both variable expansion and URI chaining."""
    provider = MockProvider(
        {
            "step1": "akv://vault/${STEP2}",
            "step2": "akv://vault/${STEP3}",
            "final": "final-value",
        }
    )
    resolver = SecretResolver({"akv": provider})
    env = {
        "STEP1": "step1",
        "STEP2": "step2",
        "STEP3": "final",
    }

    result = resolver.resolve("akv://vault/${STEP1}", env)

    assert result == "final-value"


def test_resolver_uses_os_environ_by_default() -> None:
    """Test that resolver uses os.environ when env is not provided."""
    provider = MockProvider({"test-secret": "secret-value"})
    resolver = SecretResolver({"akv": provider})

    # Temporarily set an environment variable
    original_value = os.environ.get("TEST_VAR")
    try:
        os.environ["TEST_VAR"] = "test-secret"

        result = resolver.resolve("akv://vault/${TEST_VAR}")

        assert result == "secret-value"
        assert provider.resolve_calls[0]["secret"] == "test-secret"  # noqa: S105
    finally:
        # Restore original value
        if original_value is None:
            os.environ.pop("TEST_VAR", None)
        else:
            os.environ["TEST_VAR"] = original_value
