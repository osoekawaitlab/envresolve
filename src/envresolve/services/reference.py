"""URI parsing and validation service for secret URIs."""

import re
from urllib.parse import parse_qs, urlparse

from envresolve.exceptions import URIParseError
from envresolve.models import ParsedURI

# Supported secret URI schemes
SUPPORTED_SCHEMES = {"akv"}


def is_secret_uri(uri: str) -> bool:
    """Check if a string is a valid secret URI with supported scheme.

    Args:
        uri: The URI string to check

    Returns:
        True if the URI has a supported secret scheme (akv://), False otherwise

    Examples:
        >>> is_secret_uri("akv://my-vault/secret")
        True
        >>> is_secret_uri("postgres://localhost/db")
        False
        >>> is_secret_uri("")
        False
    """
    if not uri:
        return False

    try:
        parsed = urlparse(uri)
    except Exception:  # noqa: BLE001
        return False
    else:
        return parsed.scheme in SUPPORTED_SCHEMES


def parse_secret_uri(uri: str) -> ParsedURI:
    """Parse and validate a secret URI.

    Supported formats:
    - akv://<vault-name>/<secret-name>[?version=<version>]

    Args:
        uri: The secret URI to parse

    Returns:
        Parsed URI dictionary with scheme, vault, secret, and optional version

    Raises:
        URIParseError: If the URI is invalid or not a supported secret URI

    Examples:
        >>> parse_secret_uri("akv://my-vault/db-password")
        {'scheme': 'akv', 'vault': 'my-vault', 'secret': 'db-password', 'version': None}
        >>> parse_secret_uri("akv://vault/secret?version=abc123")
        {'scheme': 'akv', 'vault': 'vault', 'secret': 'secret', 'version': 'abc123'}
    """
    if not uri:
        msg = "URI cannot be empty"
        raise URIParseError(msg, uri=uri)

    try:
        parsed = urlparse(uri)
    except Exception as e:
        msg = f"Failed to parse URI: {e}"
        raise URIParseError(msg, uri=uri) from e

    # Validate scheme
    if parsed.scheme not in SUPPORTED_SCHEMES:
        schemes_str = ", ".join(sorted(SUPPORTED_SCHEMES))
        msg = (
            f"Unsupported URI scheme '{parsed.scheme}'. "
            f"Supported schemes: {schemes_str}"
        )
        raise URIParseError(msg, uri=uri)

    # Extract vault name (netloc)
    vault_name = parsed.netloc
    if not vault_name:
        msg = "Vault name is missing"
        raise URIParseError(msg, uri=uri)

    # Validate vault name format (alphanumeric and hyphens)
    if not re.match(r"^[a-zA-Z0-9-]+$", vault_name):
        msg = (
            f"Invalid vault name '{vault_name}'. "
            "Vault names must contain only alphanumeric characters and hyphens."
        )
        raise URIParseError(msg, uri=uri)

    # Extract secret name (path without leading slash)
    secret_path = parsed.path.lstrip("/")
    if not secret_path:
        msg = "Secret name is missing"
        raise URIParseError(msg, uri=uri)

    # Extract version from query parameters
    query_params = parse_qs(parsed.query)
    version = query_params.get("version", [None])[0]

    return ParsedURI(
        scheme=parsed.scheme,
        vault=vault_name,
        secret=secret_path,
        version=version,
    )
