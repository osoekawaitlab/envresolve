"""Test envresolve package."""

import re

import envresolve


def test_version() -> None:
    """Test that the version string is valid."""
    version_pattern = r"^\d+\.\d+\.\d+([+-][\w\.]+)?$"
    assert re.match(version_pattern, envresolve.__version__), "Invalid version format"
