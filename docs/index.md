# Welcome to envresolve

Resolve environment variables from secret stores like Azure Key Vault.

## Features

- **Variable expansion**: Expand `${VAR}` and `$VAR` syntax in strings
- **Secret resolution**: Fetch secrets from Azure Key Vault (more providers coming)
- **.env support**: Load variables from `.env` files and automatically resolve secrets
- **Circular reference detection**: Prevents infinite loops in variable chains
- **Type-safe**: Full mypy type checking support

## Quick Start

### Load from .env File

The easiest way to use `envresolve` is by loading a `.env` file.

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

### Direct Secret Resolution

You can also fetch individual secrets directly:

```python
import envresolve

# Requires: pip install envresolve[azure]
try:
    envresolve.register_azure_kv_provider()
    secret_value = envresolve.resolve_secret("akv://corp-vault/db-password")
    print(secret_value)
except envresolve.ProviderRegistrationError as e:
    print(f"Azure SDK not available: {e}")
except envresolve.SecretResolutionError as e:
    print(f"Failed to fetch secret: {e}")
```

### Simple Variable Expansion

Expand variables without connecting to external services:

```python
from envresolve import expand_variables

env = {"VAULT": "corp-kv", "SECRET": "db-password"}
result = expand_variables("akv://${VAULT}/${SECRET}", env)
print(result)  # akv://corp-kv/db-password
```

## Installation

```bash
# Basic installation (variable expansion only)
pip install envresolve

# With Azure Key Vault support
pip install envresolve[azure]
```
