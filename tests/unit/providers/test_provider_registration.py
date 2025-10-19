"""Unit tests for provider registration error handling."""

from unittest.mock import MagicMock, patch

import pytest

from envresolve.api import EnvResolver
from envresolve.exceptions import ProviderRegistrationError
from envresolve.models import ParsedURI
from envresolve.providers.base import SecretProvider


def test_register_azure_kv_provider_with_custom_provider() -> None:
    """Test EnvResolver.register_azure_kv_provider accepts custom provider."""
    resolver = EnvResolver()

    # Create a mock provider
    mock_provider = MagicMock(spec=SecretProvider)
    mock_provider.resolve.return_value = "custom-secret-value"

    # Register custom provider
    resolver.register_azure_kv_provider(provider=mock_provider)

    # Verify the provider is used for resolution via public API
    result = resolver.resolve_secret("akv://test-vault/test-secret")

    # Verify the custom provider was called correctly
    assert result == "custom-secret-value"
    mock_provider.resolve.assert_called_once_with(
        ParsedURI(
            scheme="akv",
            vault="test-vault",
            secret="test-secret",  # noqa: S106
            version=None,
        )
    )


def test_register_azure_kv_provider_raises_on_import_error() -> None:
    """Test register_azure_kv_provider raises ProviderRegistrationError.

    This test verifies that when import fails, the provider raises
    ProviderRegistrationError instead of ImportError.
    """
    resolver = EnvResolver()

    with patch("envresolve.api.importlib.import_module") as mock_import:
        mock_import.side_effect = ImportError("No module named 'azure.identity'")

        with pytest.raises(ProviderRegistrationError) as exc_info:
            resolver.register_azure_kv_provider()

        # Verify error message is helpful
        error_msg = str(exc_info.value)
        assert "azure" in error_msg.lower() or "provider" in error_msg.lower()

        # Verify original ImportError is preserved as __cause__
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ImportError)
