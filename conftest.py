"""Pytest configuration for envresolve."""

import importlib.util

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    # Register azure marker
    config.addinivalue_line(
        "markers",
        "azure: mark test as requiring Azure SDK (deselect with '-m \"not azure\"')",
    )


# Check if Azure SDK is available at collection time
def _azure_sdk_available() -> bool:
    """Check if Azure SDK packages are installed."""
    try:
        return (
            importlib.util.find_spec("azure.identity") is not None
            and importlib.util.find_spec("azure.keyvault.secrets") is not None
        )
    except (ImportError, ModuleNotFoundError):
        return False


@pytest.fixture(autouse=True)
def _skip_azure_doctests(request: pytest.FixtureRequest) -> None:
    """Skip Azure-dependent doctests when Azure SDK is not available."""
    # Only apply to doctest items
    if not isinstance(request.node, pytest.DoctestItem):
        return

    # Check if this doctest is in api.py and contains Azure-related code
    if "api.py" in str(request.node.fspath):
        # Check the doctest name
        test_name = request.node.name
        azure_dependent_tests = [
            "envresolve.api.register_azure_kv_provider",
            "envresolve.api.load_env",
            "envresolve.api.resolve_os_environ",
        ]

        is_azure_test = any(name in test_name for name in azure_dependent_tests)
        if is_azure_test and not _azure_sdk_available():
            pytest.skip("Azure SDK not available")
