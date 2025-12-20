# envresolve

Resolve environment variables from secret stores like Azure Key Vault.

## Features

- **Variable expansion**: Expand `${VAR}` and `$VAR` syntax in strings
- **Secret resolution**: Fetch secrets from Azure Key Vault (more providers coming)
- **Circular reference detection**: Prevents infinite loops in variable chains
- **Type-safe**: Full mypy type checking support

## Quick Start

### Variable Expansion

Expand variables without connecting to external services:

```python
from envresolve import expand_variables

env = {"VAULT": "corp-kv", "SECRET": "db-password"}
result = expand_variables("akv://${VAULT}/${SECRET}", env)
print(result)  # akv://corp-kv/db-password
```

### Default Values

Use default values for undefined or empty variables with `${VAR:-default}` syntax:

```python
from envresolve import expand_variables

# Variable is undefined - use default
result = expand_variables("${HOST:-localhost}", {})
print(result)  # localhost

# Variable is empty - use default (Bash :- semantics)
result = expand_variables("${HOST:-localhost}", {"HOST": ""})
print(result)  # localhost

# Variable is defined - ignore default
result = expand_variables("${HOST:-localhost}", {"HOST": "example.com"})
print(result)  # example.com

# Defaults can contain nested variables
env = {"FALLBACK_HOST": "backup.example.com"}
result = expand_variables("${HOST:-${FALLBACK_HOST}}", env)
print(result)  # backup.example.com

# Multiple defaults in one string
result = expand_variables("${PROTO:-https}://${HOST:-localhost}:${PORT:-443}", {})
print(result)  # https://localhost:443
```

### Load from .env File

Load environment variables from a `.env` file with automatic secret resolution:

```python
import envresolve

# .env file content:
# VAULT_NAME=my-vault
# DATABASE_URL=akv://${VAULT_NAME}/db-url
# API_KEY=akv://${VAULT_NAME}/api-key

# Requires: pip install envresolve[azure]
# Requires: Azure authentication (az login, Managed Identity, etc.)
envresolve.register_azure_kv_provider()

# Load .env and resolve all secret URIs
# By default, searches for .env in current directory and exports to os.environ
resolved_vars = envresolve.load_env()

# Or specify explicit path and disable export
resolved_vars = envresolve.load_env(dotenv_path=".env", export=False)
```

**Note**: For complete python-dotenv compatibility, use `load_dotenv()` + `resolve_os_environ()`:

```python
from dotenv import load_dotenv
import envresolve

# Use python-dotenv's search behavior (from calling script location)
load_dotenv()

# Resolve secrets in os.environ
envresolve.register_azure_kv_provider()
envresolve.resolve_os_environ()
```

### Direct Secret Resolution

Fetch individual secrets from Azure Key Vault:

```python
import envresolve

# Requires: pip install envresolve[azure]
# Requires: Azure authentication (az login, Managed Identity, etc.)
try:
    envresolve.register_azure_kv_provider()
    secret_value = envresolve.resolve_secret("akv://corp-vault/db-password")
    print(secret_value)
except envresolve.ProviderRegistrationError as e:
    print(f"Azure SDK not available: {e}")
except envresolve.SecretResolutionError as e:
    print(f"Failed to fetch secret: {e}")
```

### Custom Provider Configuration

Inject custom provider instances for advanced scenarios (testing, custom credentials, etc.):

```python
import envresolve
from envresolve.providers.azure_kv import AzureKVProvider
from azure.identity import ManagedIdentityCredential

# Create custom provider with specific credential
custom_provider = AzureKVProvider(
    credential=ManagedIdentityCredential(client_id="your-client-id")
)

# Register the custom provider
envresolve.register_azure_kv_provider(provider=custom_provider)

# Now use envresolve as normal
secret = envresolve.resolve_secret("akv://vault/secret")
```

This is particularly useful for:

- **Testing**: Inject mock providers without patching internal implementation details
- **Custom authentication**: Use specific Azure credentials (service principal, managed identity, etc.)
- **Provider configuration**: Pre-configure providers with custom settings

### Resolve Existing Environment Variables

Resolve secret URIs already set in `os.environ` (useful for containerized applications):

```python
import os
import envresolve

# Environment variables set by container orchestrator or parent process
os.environ["API_KEY"] = "akv://prod-vault/api-key"
os.environ["DB_PASSWORD"] = "akv://prod-vault/db-password"

# Requires: pip install envresolve[azure]
envresolve.register_azure_kv_provider()

# Resolve all environment variables containing secret URIs
resolved = envresolve.resolve_os_environ()

# Resolve only specific keys
resolved = envresolve.resolve_os_environ(keys=["API_KEY"])

# Resolve variables with prefix and strip the prefix
# DEV_API_KEY -> API_KEY, DEV_DB_URL -> DB_URL
os.environ["DEV_API_KEY"] = "akv://dev-vault/api-key"
os.environ["DEV_DB_URL"] = "akv://dev-vault/db-url"
resolved = envresolve.resolve_os_environ(prefix="DEV_")

# Ignore specific variables (exact match)
os.environ["PS1"] = "${USER}@${HOST}$ "  # Should not be expanded
os.environ["API_KEY"] = "akv://vault/api-key"
resolved = envresolve.resolve_os_environ(ignore_keys=["PS1"])

# Ignore variables by pattern (glob matching)
os.environ["PS1"] = "${USER}@${HOST}$ "
os.environ["PS2"] = "> "
os.environ["PROMPT"] = "${PWD}$ "
os.environ["API_KEY"] = "akv://vault/api-key"
resolved = envresolve.resolve_os_environ(ignore_patterns=["PS*", "PROMPT*"])

# Combine exact match and patterns
resolved = envresolve.resolve_os_environ(
    ignore_keys=["SPECIFIC_VAR"],
    ignore_patterns=["TEMP_*", "DEBUG_*"]
)
```

### Error Handling

Resolution errors include context about which environment variable failed:

```python
import envresolve

try:
    envresolve.load_env(dotenv_path=".env", export=False)
except envresolve.EnvironmentVariableResolutionError as e:
    print(f"Failed variable: {e.context_key}")
    print(f"Cause: {e.original_error}")
```

Control error behavior:

```python
# Skip variables with expansion errors
resolved = envresolve.load_env(stop_on_expansion_error=False)

# Skip variables with secret resolution errors
resolved = envresolve.load_env(stop_on_resolution_error=False)
```

## Installation

```bash
# Basic installation (variable expansion only)
pip install envresolve

# With Azure Key Vault support
pip install envresolve[azure]
```

## Documentation

Full documentation: <https://osoekawaitlab.github.io/envresolve/>

## Development

### Setup

This project uses `uv` for dependency management and `nox` for task automation:

```bash
# Install uv (if not already installed)
pip install uv

# Clone the repository
git clone https://github.com/osoekawaitlab/envresolve.git
cd envresolve

# Install dependencies and create virtual environment
uv sync --all-extras --all-groups

# Activate virtual environment
source .venv/bin/activate  # On Unix/macOS
# .venv\Scripts\activate   # On Windows
```

### Running Tests

```bash
# Quick test during development
nox -s tests_unit      # Unit tests only (fast)
nox -s tests_e2e       # E2E tests with mocked Azure SDK

# Full test suite
nox -s tests           # All tests with coverage report (HTML in htmlcov/)

# Test across Python versions
nox -s tests_all_versions  # Test on Python 3.10-3.14

# Test without Azure SDK
nox -s tests_without_azure  # For environments without Azure dependencies
```

### Code Quality

```bash
# Run all quality checks
nox -s quality         # Type checking (mypy) + linting (ruff)

# Individual checks
nox -s mypy            # Type checking only
nox -s lint            # Linting only
nox -s format_code     # Auto-format code

# Run everything
nox -s check_all       # Tests + quality checks
```

### Live Azure Tests

Optional integration tests against real Azure Key Vault:

```bash
# One-time setup
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your Azure credentials
terraform init
terraform apply

# Before running tests
az login
source scripts/setup_live_tests.sh

# Run live tests
nox -s tests_live
```

See [Live Azure Tests documentation](https://osoekawaitlab.github.io/envresolve/developer-guide/live-tests/) for detailed setup instructions.

### Build Documentation

```bash
# Build documentation
nox -s docs_build

# Serve documentation locally (with live reload)
mkdocs serve           # Open http://localhost:8000
```

### Contributing

See [Contributing Guide](https://osoekawaitlab.github.io/envresolve/developer-guide/contributing/) for guidelines on:

- Code style and conventions
- Test-driven development workflow
- Creating issues and pull requests
- Architecture Decision Records (ADRs)
