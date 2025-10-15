"""E2E tests for provider registration error handling."""

from unittest.mock import patch

import pytest

import envresolve


def test_register_azure_kv_provider_raises_on_missing_deps() -> None:
    """Test register_azure_kv_provider raises ProviderRegistrationError.

    When Azure SDK is missing, this test verifies the acceptance criteria:
    - register_azure_kv_provider() raises ProviderRegistrationError
      instead of ImportError
    - Original ImportError is preserved as __cause__
    """
    # Mock importlib.import_module to simulate missing Azure SDK
    with patch("envresolve.api.importlib.import_module") as mock_import:
        mock_import.side_effect = ImportError("No module named 'azure.identity'")

        # Should raise ProviderRegistrationError, not ImportError
        with pytest.raises(envresolve.ProviderRegistrationError) as exc_info:
            envresolve.register_azure_kv_provider()

        # Verify error message is helpful
        error_msg = str(exc_info.value)
        assert "azure" in error_msg.lower() or "provider" in error_msg.lower()

        # Verify original ImportError is preserved as __cause__
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ImportError)


def test_provider_registration_error_inherits_from_env_resolve_error() -> None:
    """Test that ProviderRegistrationError can be caught as EnvResolveError.

    This verifies the "Selective error handling" benefit from ADR-0002.
    """
    with patch("envresolve.api.importlib.import_module") as mock_import:
        mock_import.side_effect = ImportError("No module named 'azure.identity'")

        # Should be catchable as EnvResolveError
        with pytest.raises(envresolve.EnvResolveError):
            envresolve.register_azure_kv_provider()
