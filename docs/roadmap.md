# Roadmap

## Current Version: 0.1.0

### Completed Features

- ✅ Variable expansion with `${VAR}` and `$VAR` syntax
- ✅ Circular reference detection
- ✅ Nested variable expansion
- ✅ Support for `os.environ`, `.env` files, and custom dictionaries

## Planned Features

### v0.1.x (In Progress)

- Secret URI resolution (e.g., `akv://vault-name/secret-name`)
- Azure Key Vault provider
- Simple API: `load_env()`, `resolve_secret()`

### v0.2.x

- CLI tool (`envresolve render`)
- pydantic-settings integration
- Secret caching with TTL

### v0.3.x+

- Additional secret providers:
  - AWS Secrets Manager / SSM Parameter Store
  - Google Secret Manager
  - HashiCorp Vault
  - Local: 1Password, Bitwarden, pass, sops
- Async support for concurrent secret resolution
