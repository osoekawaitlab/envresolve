"""E2E tests for load_env function."""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

import envresolve
from envresolve.providers.base import SecretProvider


@pytest.fixture
def temp_env_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary directory and change cwd to it for the test.

    Returns the temporary directory path.
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_load_env_with_dotenv_path_none_finds_dotenv_in_cwd(
    temp_env_dir: Path,
) -> None:
    """Test load_env() with dotenv_path=None finds .env in current directory.

    This mimics python-dotenv's load_dotenv() behavior where None means
    search for .env file.
    """
    env_file = temp_env_dir / ".env"
    env_file.write_text("TEST_VAR=test_value\nANOTHER_VAR=another_value\n")

    result = envresolve.load_env(dotenv_path=None, export=False)

    assert result == {"TEST_VAR": "test_value", "ANOTHER_VAR": "another_value"}


def test_load_env_with_no_args_finds_dotenv_in_cwd(temp_env_dir: Path) -> None:
    """Test load_env() with no arguments finds .env in current directory.

    Default behavior should match python-dotenv's load_dotenv().
    """
    env_file = temp_env_dir / ".env"
    env_file.write_text("HELLO=world\n")

    result = envresolve.load_env(export=False)

    assert result == {"HELLO": "world"}


@pytest.mark.usefixtures("temp_env_dir")
def test_load_env_with_dotenv_path_none_returns_empty_when_no_file() -> None:
    """Test load_env() returns empty dict when .env doesn't exist."""
    result = envresolve.load_env(dotenv_path=None, export=False)

    assert result == {}


def test_load_env_with_explicit_path(tmp_path: Path) -> None:
    """Test load_env() with explicit dotenv_path parameter."""
    env_file = tmp_path / "custom.env"
    env_file.write_text("CUSTOM=value\n")

    result = envresolve.load_env(dotenv_path=str(env_file), export=False)

    assert result == {"CUSTOM": "value"}


def test_load_env_with_explicit_path_as_pathlike(tmp_path: Path) -> None:
    """Test load_env() accepts Path objects."""
    env_file = tmp_path / "path.env"
    env_file.write_text("PATHLIKE=works\n")

    result = envresolve.load_env(dotenv_path=env_file, export=False)

    assert result == {"PATHLIKE": "works"}


def test_load_env_export_to_os_environ(
    temp_env_dir: Path, mocker: MockerFixture
) -> None:
    """Test load_env() exports variables to os.environ when export=True."""
    env_file = temp_env_dir / ".env"
    env_file.write_text("EXPORT_TEST=exported\n")

    # Mock os.environ as empty dict
    mocker.patch.dict("os.environ", {}, clear=True)

    result = envresolve.load_env(export=True)

    assert result == {"EXPORT_TEST": "exported"}
    assert os.environ["EXPORT_TEST"] == "exported"


def test_load_env_export_respects_override_false(
    temp_env_dir: Path, mocker: MockerFixture
) -> None:
    """Test load_env() doesn't override existing env vars when override=False."""
    env_file = temp_env_dir / ".env"
    env_file.write_text("EXISTING_VAR=new_value\n")

    # Mock os.environ with existing value
    mocker.patch.dict("os.environ", {"EXISTING_VAR": "old_value"}, clear=True)

    result = envresolve.load_env(export=True, override=False)

    assert result == {"EXISTING_VAR": "new_value"}
    # Should NOT override existing value
    assert os.environ["EXISTING_VAR"] == "old_value"


def test_load_env_export_respects_override_true(
    temp_env_dir: Path, mocker: MockerFixture
) -> None:
    """Test load_env() overrides existing env vars when override=True."""
    env_file = temp_env_dir / ".env"
    env_file.write_text("OVERRIDE_VAR=new_value\n")

    # Mock os.environ with existing value
    mocker.patch.dict("os.environ", {"OVERRIDE_VAR": "old_value"}, clear=True)

    result = envresolve.load_env(export=True, override=True)

    assert result == {"OVERRIDE_VAR": "new_value"}
    # Should override existing value
    assert os.environ["OVERRIDE_VAR"] == "new_value"


def test_load_env_with_variable_expansion(temp_env_dir: Path) -> None:
    """Test load_env() expands variable references."""
    env_file = temp_env_dir / ".env"
    env_file.write_text("BASE=hello\nDERIVED=${BASE}_world\n")

    result = envresolve.load_env(export=False)

    assert result == {"BASE": "hello", "DERIVED": "hello_world"}


def test_load_env_with_os_environ_variable_expansion(
    temp_env_dir: Path, mocker: MockerFixture
) -> None:
    """Test load_env() can expand variables from os.environ."""
    env_file = temp_env_dir / ".env"
    env_file.write_text("EXPANDED=${OS_VAR}_suffix\n")

    # Mock os.environ with OS_VAR
    mocker.patch.dict("os.environ", {"OS_VAR": "prefix"}, clear=True)

    result = envresolve.load_env(export=False)

    assert result == {"EXPANDED": "prefix_suffix"}


@pytest.mark.azure
def test_load_env_with_akv_uri_resolution(temp_env_dir: Path) -> None:
    """Test load_env() resolves Azure Key Vault URIs.

    This test requires Azure SDK to be installed.
    """
    env_file = temp_env_dir / ".env"
    env_file.write_text("SECRET=akv://test-vault/test-secret\n")

    # Mock the Azure provider
    mock_provider = MagicMock(spec=SecretProvider)
    mock_provider.resolve.return_value = "secret-value"

    envresolve.register_azure_kv_provider(provider=mock_provider)

    result = envresolve.load_env(export=False)

    assert result == {"SECRET": "secret-value"}


def test_load_env_with_complex_scenario(temp_env_dir: Path) -> None:
    """Test load_env() with variable expansion and multiple variables.

    Complex real-world scenario with:
    - Plain values
    - Variable references
    - Nested variable expansion
    """
    env_file = temp_env_dir / ".env"
    env_file.write_text(
        """
# Configuration
ENVIRONMENT=production
REGION=us-east-1

# Derived values
VAULT_NAME=${ENVIRONMENT}-${REGION}-vault
APP_NAME=myapp

# Complex references
DATABASE_URL=postgres://${APP_NAME}:secret@${VAULT_NAME}.db
API_ENDPOINT=https://api.${ENVIRONMENT}.example.com
"""
    )

    result = envresolve.load_env(export=False)

    assert result == {
        "ENVIRONMENT": "production",
        "REGION": "us-east-1",
        "VAULT_NAME": "production-us-east-1-vault",
        "APP_NAME": "myapp",
        "DATABASE_URL": "postgres://myapp:secret@production-us-east-1-vault.db",
        "API_ENDPOINT": "https://api.production.example.com",
    }


def test_load_env_empty_file_returns_empty_dict(temp_env_dir: Path) -> None:
    """Test load_env() returns empty dict for empty .env file."""
    env_file = temp_env_dir / ".env"
    env_file.write_text("")

    result = envresolve.load_env(export=False)

    assert result == {}


def test_load_env_filters_none_values(temp_env_dir: Path) -> None:
    """Test load_env() filters out None values from dotenv parsing.

    python-dotenv returns None for lines without values.
    """
    env_file = temp_env_dir / ".env"
    # Lines with comments or no value should not appear in result
    env_file.write_text("# Comment\nVALID=value\n# COMMENTED=out\n")

    result = envresolve.load_env(export=False)

    assert result == {"VALID": "value"}
    assert "COMMENTED" not in result


def test_load_env_expansion_error_raised_by_default(
    temp_env_dir: Path, mocker: MockerFixture
) -> None:
    """Test load_env() raises EnvironmentVariableResolutionError by default."""
    env_file = temp_env_dir / ".env"
    env_file.write_text("VALID=hello\nINVALID=${NONEXISTENT}\n")

    # Clear os.environ to ensure NONEXISTENT doesn't exist anywhere
    mocker.patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True)

    with pytest.raises(envresolve.EnvironmentVariableResolutionError) as exc_info:
        envresolve.load_env(dotenv_path=env_file, export=False)

    assert "NONEXISTENT" in str(exc_info.value)
    assert exc_info.value.context_key == "INVALID"
    assert isinstance(exc_info.value.original_error, envresolve.VariableNotFoundError)


def test_load_env_expansion_error_suppressed(
    temp_env_dir: Path, mocker: MockerFixture
) -> None:
    """Test load_env() skips variables with expansion errors.

    Tests that stop_on_expansion_error=False skips expansion errors.
    """
    env_file = temp_env_dir / ".env"
    env_file.write_text("VALID=hello\nINVALID=${NONEXISTENT}\nALSO_VALID=world\n")

    mocker.patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True)

    result = envresolve.load_env(
        dotenv_path=env_file, export=False, stop_on_expansion_error=False
    )

    # Only valid variables should be resolved
    assert result == {"VALID": "hello", "ALSO_VALID": "world"}
    assert "INVALID" not in result


def test_load_env_circular_reference_error_raised_by_default(
    temp_env_dir: Path, mocker: MockerFixture
) -> None:
    """Test load_env() raises CircularReferenceError by default."""
    env_file = temp_env_dir / ".env"
    env_file.write_text("A=${B}\nB=${A}\n")

    mocker.patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True)

    with pytest.raises(envresolve.CircularReferenceError):
        envresolve.load_env(dotenv_path=env_file, export=False)


def test_load_env_resolution_error_raised_by_default(
    temp_env_dir: Path, mocker: MockerFixture
) -> None:
    """Test load_env() raises EnvironmentVariableResolutionError by default."""
    env_file = temp_env_dir / ".env"
    env_file.write_text("VALID=hello\nSECRET=akv://test-vault/secret\n")

    # Register mock provider that raises SecretResolutionError
    mock_provider = MagicMock(spec=SecretProvider)
    mock_provider.resolve.side_effect = envresolve.SecretResolutionError(
        "Failed to fetch secret", "akv://test-vault/secret"
    )
    envresolve.register_azure_kv_provider(provider=mock_provider)

    mocker.patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True)

    with pytest.raises(envresolve.EnvironmentVariableResolutionError) as exc_info:
        envresolve.load_env(dotenv_path=env_file, export=False)

    assert "Failed to fetch secret" in str(exc_info.value)
    assert exc_info.value.context_key == "SECRET"
    assert isinstance(exc_info.value.original_error, envresolve.SecretResolutionError)


def test_load_env_resolution_error_suppressed(
    temp_env_dir: Path, mocker: MockerFixture
) -> None:
    """Test load_env() skips variables with resolution errors.

    Tests that stop_on_resolution_error=False skips resolution errors.
    """
    env_file = temp_env_dir / ".env"
    env_file.write_text(
        "VALID=hello\nSECRET=akv://test-vault/secret\nALSO_VALID=world\n"
    )

    # Register mock provider that raises SecretResolutionError
    mock_provider = MagicMock(spec=SecretProvider)
    mock_provider.resolve.side_effect = envresolve.SecretResolutionError(
        "Failed to fetch secret", "akv://test-vault/secret"
    )
    envresolve.register_azure_kv_provider(provider=mock_provider)

    mocker.patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True)

    result = envresolve.load_env(
        dotenv_path=env_file, export=False, stop_on_resolution_error=False
    )

    # Only variables without resolution errors should be resolved
    assert result == {"VALID": "hello", "ALSO_VALID": "world"}
    assert "SECRET" not in result


def test_load_env_both_errors_suppressed(
    temp_env_dir: Path, mocker: MockerFixture
) -> None:
    """Test load_env() with both error flags set to False.

    Verifies that VariableNotFoundError is suppressed,
    SecretResolutionError is suppressed, but CircularReferenceError
    is always raised (configuration error).
    """
    env_file = temp_env_dir / ".env"
    env_file.write_text(
        "VALID=hello\n"
        "EXPANSION_ERROR=${NONEXISTENT}\n"
        "SECRET=akv://test-vault/secret\n"
        "CIRCULAR_A=${CIRCULAR_B}\n"
        "CIRCULAR_B=${CIRCULAR_A}\n"
        "ALSO_VALID=world\n"
    )

    # Register mock provider that raises SecretResolutionError
    mock_provider = MagicMock(spec=SecretProvider)
    mock_provider.resolve.side_effect = envresolve.SecretResolutionError(
        "Failed to fetch secret", "akv://test-vault/secret"
    )
    envresolve.register_azure_kv_provider(provider=mock_provider)

    mocker.patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True)

    # CircularReferenceError should still be raised
    with pytest.raises(envresolve.CircularReferenceError):
        envresolve.load_env(
            dotenv_path=env_file,
            export=False,
            stop_on_expansion_error=False,
            stop_on_resolution_error=False,
        )


def test_load_env_both_errors_raised(temp_env_dir: Path, mocker: MockerFixture) -> None:
    """Test load_env() raises first error encountered.

    Tests that both flags set to True (default) raise the first error wrapped.
    """
    env_file = temp_env_dir / ".env"
    # Put expansion error first
    env_file.write_text("EXPANSION_ERROR=${NONEXISTENT}\nVALID=hello\n")

    mocker.patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True)

    # Should raise expansion error (first in the file), wrapped
    with pytest.raises(envresolve.EnvironmentVariableResolutionError) as exc_info:
        envresolve.load_env(dotenv_path=env_file, export=False)

    assert exc_info.value.context_key == "EXPANSION_ERROR"
    assert isinstance(exc_info.value.original_error, envresolve.VariableNotFoundError)


def test_load_env_with_ignore_keys(temp_env_dir: Path, mocker: MockerFixture) -> None:
    """Test load_env() with ignore_keys parameter.

    Acceptance criteria:
    - ignore_keys parameter skips expansion for specified keys
    - Ignored variables are included in result as-is
    """
    env_file = temp_env_dir / ".env"
    env_file.write_text("CONFIG=${UNDEFINED_VAR}\nVALID=hello\n")

    mocker.patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True)

    result = envresolve.load_env(
        dotenv_path=env_file, export=False, ignore_keys=["CONFIG"]
    )

    assert result["CONFIG"] == "${UNDEFINED_VAR}"  # Unchanged, not expanded
    assert result["VALID"] == "hello"


def test_load_env_wraps_expansion_error_with_context(
    temp_env_dir: Path, mocker: MockerFixture
) -> None:
    """Test that load_env() wraps VariableNotFoundError with context.

    Acceptance criteria:
    - EnvironmentVariableResolutionError includes context_key
    - Original VariableNotFoundError is preserved
    - Error message includes both variable name and context
    """
    env_file = temp_env_dir / ".env"
    env_file.write_text("VAR1=hello\nVAR2=${UNDEFINED}\nVAR3=world\n")

    mocker.patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True)

    with pytest.raises(envresolve.EnvironmentVariableResolutionError) as exc_info:
        envresolve.load_env(dotenv_path=env_file, export=False)

    # Check attributes
    assert exc_info.value.context_key == "VAR2"
    assert isinstance(exc_info.value.original_error, envresolve.VariableNotFoundError)

    # Check error message includes context
    assert "VAR2" in str(exc_info.value)
    assert "UNDEFINED" in str(exc_info.value)


def test_load_env_with_ignore_patterns(
    temp_env_dir: Path, mocker: MockerFixture
) -> None:
    """Test load_env() with ignore_patterns parameter.

    Acceptance criteria:
    - ignore_patterns parameter skips expansion for keys matching glob patterns
    - Ignored variables are included in result as-is
    """
    env_file = temp_env_dir / ".env"
    env_file.write_text("PS1=${UNDEFINED}\nPS2=${ALSO_UNDEFINED}\nVALID=hello\n")

    mocker.patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True)

    result = envresolve.load_env(
        dotenv_path=env_file, export=False, ignore_patterns=["PS*"]
    )

    assert result["PS1"] == "${UNDEFINED}"  # Unchanged, pattern matched
    assert result["PS2"] == "${ALSO_UNDEFINED}"  # Unchanged, pattern matched
    assert result["VALID"] == "hello"


def test_load_env_with_multiple_ignore_patterns(
    temp_env_dir: Path, mocker: MockerFixture
) -> None:
    """Test load_env() with multiple ignore patterns (real-world use case).

    Acceptance criteria:
    - Multiple patterns can be specified
    - Variables matching any pattern are ignored
    - Demonstrates real-world usage (TEMP_*, PROMPT*, DEBUG_*)
    """
    env_file = temp_env_dir / ".env"
    env_file.write_text(
        "TEMP_VAR=${UNDEFINED1}\n"
        "TEMP_FILE=${UNDEFINED2}\n"
        "PROMPT=${UNDEFINED3}\n"
        "PROMPT_COMMAND=${UNDEFINED4}\n"
        "DEBUG_MODE=${UNDEFINED5}\n"
        "VALID_VAR=production\n"
    )

    mocker.patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True)

    result = envresolve.load_env(
        dotenv_path=env_file,
        export=False,
        ignore_patterns=["TEMP_*", "PROMPT*", "DEBUG_*"],
    )

    # All temporary, prompt, and debug variables should be unchanged
    assert result["TEMP_VAR"] == "${UNDEFINED1}"
    assert result["TEMP_FILE"] == "${UNDEFINED2}"
    assert result["PROMPT"] == "${UNDEFINED3}"
    assert result["PROMPT_COMMAND"] == "${UNDEFINED4}"
    assert result["DEBUG_MODE"] == "${UNDEFINED5}"
    # Valid variable should be processed
    assert result["VALID_VAR"] == "production"


def test_load_env_with_both_ignore_keys_and_patterns(
    temp_env_dir: Path, mocker: MockerFixture
) -> None:
    """Test load_env() with both ignore_keys and ignore_patterns.

    Acceptance criteria:
    - ignore_keys and ignore_patterns work together
    - Variables matching either are ignored
    - Union of both exclusion methods
    """
    env_file = temp_env_dir / ".env"
    env_file.write_text(
        "SPECIFIC_VAR=${UNDEFINED1}\n"  # Exact match via ignore_keys
        "PS1=${UNDEFINED2}\n"  # Pattern match via ignore_patterns
        "PS2=${UNDEFINED3}\n"  # Pattern match via ignore_patterns
        "VALID_VAR=hello\n"
    )

    mocker.patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True)

    result = envresolve.load_env(
        dotenv_path=env_file,
        export=False,
        ignore_keys=["SPECIFIC_VAR"],
        ignore_patterns=["PS*"],
    )

    # SPECIFIC_VAR ignored by exact match
    assert result["SPECIFIC_VAR"] == "${UNDEFINED1}"
    # PS1 and PS2 ignored by pattern match
    assert result["PS1"] == "${UNDEFINED2}"
    assert result["PS2"] == "${UNDEFINED3}"
    # VALID_VAR processed normally
    assert result["VALID_VAR"] == "hello"
