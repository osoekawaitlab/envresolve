"""Unit tests for provider registration error handling."""

from unittest.mock import patch

import pytest

from envresolve.api import EnvResolver
from envresolve.exceptions import ProviderRegistrationError


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
