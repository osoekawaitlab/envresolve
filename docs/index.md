# envresolve

**envresolve** is a Python library for resolving environment variables from secret stores (e.g., Azure Key Vault).

## Features

- **Variable Expansion**: Support for `${VAR}` and `$VAR` syntax with nested expansion
- **Circular Reference Detection**: Automatically detects and prevents circular variable references
- **Multiple Sources**: Works with `os.environ`, `.env` files, or custom dictionaries
- **Type Safe**: Built with strict type checking using mypy
- **Well Tested**: 100% test coverage with comprehensive unit and E2E tests

## Quick Start

### Installation

```bash
pip install envresolve
```

### Basic Example

```python
from envresolve import expand_variables

# Simple variable expansion
env = {"VAULT_NAME": "my-vault"}
result = expand_variables("akv://${VAULT_NAME}/secret", env)
# Result: "akv://my-vault/secret"

# Nested variable expansion
env = {
    "VAULT": "my-vault",
    "SECRET_PATH": "${VAULT}/db-password",
    "FULL_URI": "akv://${SECRET_PATH}"
}
result = expand_variables(env["FULL_URI"], env)
# Result: "akv://my-vault/db-password"
```

### Using with os.environ

```python
from envresolve import EnvExpander

expander = EnvExpander()
result = expander.expand("akv://${VAULT_NAME}/secret")
# Expands using current environment variables
```

### Using with .env files

```python
from envresolve import DotEnvExpander

expander = DotEnvExpander(".env")
result = expander.expand("akv://${VAULT_NAME}/secret")
# Expands using variables from .env file
```

## Project Status

**Current Version**: 0.1.0 (Variable Expansion - Phase 2)

envresolve is under active development. Currently implemented:

- ✅ Variable expansion with `${VAR}` and `$VAR` syntax
- ✅ Circular reference detection
- ✅ Nested variable expansion
- ⏳ URI parsing and secret provider system (coming soon)

See [Roadmap](roadmap.md) for full development plan.

## Documentation

- [User Guide](user-guide/installation.md) - Installation and usage instructions
- [API Reference](api-reference/expansion.md) - Detailed API documentation
- [Architecture](architecture/adr.md) - Design decisions and ADRs
- [Contributing](contributing.md) - Development guide

## License

MIT
