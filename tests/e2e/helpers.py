"""Helpers for end-to-end tests."""

import logging

from envresolve import SecretResolutionError
from envresolve.models import ParsedURI
from envresolve.providers.base import SecretProvider


class MockProvider(SecretProvider):
    """Mock secret provider for testing."""

    def resolve(
        self,
        parsed_uri: ParsedURI,
        logger: logging.Logger | None = None,
    ) -> str:
        """Mock resolve method."""
        if parsed_uri["vault"] != "fake-vault":
            if logger is not None:
                logger.debug("MockProvider resolving secret")
        else:
            msg = "vault 'fake-vault' is not accessible"
            raise SecretResolutionError(msg, uri=str(parsed_uri))
        return "mock-secret-value"
