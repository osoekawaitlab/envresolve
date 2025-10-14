# Roadmap

## Current Version: 0.1.0

### Completed Features

- ✅ Variable expansion with `${VAR}` and `$VAR` syntax
- ✅ Circular reference detection
- ✅ Nested variable expansion
- ✅ Support for `os.environ`, `.env` files, and custom dictionaries
- ✅ Secret URI resolution with Azure Key Vault provider (`resolve_secret`, `load_env`)

## Planned Features

### v0.1.x (In Progress)

- Validation helpers for string-based API (`is_resolved`, `needs_expansion`, `is_secret_uri`)
- Optional metadata/query helpers for resolved values
- Structured logging hooks for resolution diagnostics

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
