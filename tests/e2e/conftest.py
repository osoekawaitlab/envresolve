"""Shared fixtures for E2E tests."""

from collections.abc import Iterator

import pytest

import envresolve.api


@pytest.fixture(autouse=True)
def reset_default_resolver() -> Iterator[None]:
    """Fixture to automatically reset the global default resolver's state.

    This ensures test isolation by resetting providers between tests.
    """
    # Save the original state before the test runs
    original_providers = envresolve.api._default_resolver._providers.copy()  # noqa: SLF001
    original_resolver = envresolve.api._default_resolver._resolver  # noqa: SLF001

    yield  # Test runs here

    # Restore the original state after the test completes
    envresolve.api._default_resolver._providers = original_providers  # noqa: SLF001
    envresolve.api._default_resolver._resolver = original_resolver  # noqa: SLF001
