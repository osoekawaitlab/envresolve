"""Domain models for envresolve.

This module contains pure domain models with no dependencies on other layers.
"""

from typing import TypedDict


class ParsedURI(TypedDict):
    """Parsed and validated secret URI.

    Attributes:
        scheme: URI scheme (e.g., "akv", "kv")
        vault: Vault name
        secret: Secret name
        version: Optional secret version
    """

    scheme: str
    vault: str
    secret: str
    version: str | None
