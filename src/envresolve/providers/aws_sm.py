"""AWS Secrets Manager provider implementation."""

import logging
from typing import TYPE_CHECKING

import boto3
from botocore.exceptions import ClientError

from envresolve.exceptions import SecretResolutionError
from envresolve.models import ParsedURI

if TYPE_CHECKING:
    from boto3 import Session
    from mypy_boto3_secretsmanager import SecretsManagerClient


class AWSSecretsManagerProvider:
    """Provider for resolving secrets from AWS Secrets Manager.

    Supports asm:// URI scheme.
    Uses default AWS credential chain for authentication.
    Caches client instances per region for efficiency.
    """

    def __init__(
        self,
        session: "Session | None" = None,
        region_name: str | None = None,
    ) -> None:
        """Initialize AWS Secrets Manager provider.

        Args:
            session: boto3 Session to use. If None, uses default session.
            region_name: AWS region name. If None, uses default region from
                environment or AWS config.
        """
        self._session = session
        self._region_name = region_name
        self._clients: dict[str | None, "SecretsManagerClient"] = {}

    def _get_client(self, region: str | None = None) -> "SecretsManagerClient":
        """Get or create a SecretsManager client for the given region.

        Args:
            region: AWS region name. If None, uses instance default.

        Returns:
            SecretsManagerClient instance for the region
        """
        effective_region = region or self._region_name

        if effective_region not in self._clients:
            if self._session is not None:
                # Use provided session
                self._clients[effective_region] = self._session.client(
                    "secretsmanager",
                    region_name=effective_region,
                )
            else:
                # Use default session
                self._clients[effective_region] = boto3.client(
                    "secretsmanager",
                    region_name=effective_region,
                )
        return self._clients[effective_region]

    def resolve(
        self,
        parsed_uri: ParsedURI,
        logger: logging.Logger | None = None,  # noqa: ARG002
    ) -> str:
        """Resolve a secret from AWS Secrets Manager.

        Args:
            parsed_uri: Parsed URI dictionary containing vault (secret name),
                secret (ignored for AWS), and optional version
            logger: Optional logger for diagnostic messages

        Returns:
            The secret value as a string

        Raises:
            SecretResolutionError: If the secret cannot be resolved

        Note:
            For AWS Secrets Manager, the URI format is:
            asm://<secret-name>/<ignored>?version=<version-id-or-stage>

            The 'vault' field contains the secret name.
            The 'secret' field is required by ParsedURI but ignored for AWS.
            The 'version' field can be a version ID or version stage.
        """
        secret_name = parsed_uri["vault"]
        version = parsed_uri["version"]

        # Reconstruct URI for error messages
        uri = f"{parsed_uri['scheme']}://{secret_name}/{parsed_uri['secret']}"
        if version:
            uri = f"{uri}?version={version}"

        try:
            client = self._get_client()

            # Build request parameters
            request_params: dict[str, str] = {"SecretId": secret_name}
            if version:
                # Version can be either a version ID or a version stage
                # AWS uses VersionId for specific versions and VersionStage for labels
                # Try VersionId first as it's more specific
                request_params["VersionId"] = version

            response = client.get_secret_value(**request_params)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            msg = f"Failed to resolve secret from AWS Secrets Manager: {error_code}"
            raise SecretResolutionError(msg, uri=uri, original_error=e) from e

        # AWS Secrets Manager can return either SecretString or SecretBinary.
        # Type stubs define both as required; in reality they're mutually exclusive.
        secret_string: str | None = response.get("SecretString")
        if secret_string is not None:
            return secret_string
        msg = "Secret is binary, not a string"
        raise SecretResolutionError(msg, uri=uri)
