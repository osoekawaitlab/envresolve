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

- Structured logging hooks for resolution diagnostics
- Variable ignore patterns for error handling:
    - Function parameter: `ignore_keys`, `ignore_patterns`
    - Pattern matching support (e.g., `PS*`, `PROMPT*`)
    - Environment variable configuration: `ENVRESOLVE_IGNORE`
    - Use case: Skip system variables like `$PS1`, `%PROMPT%` that contain `$` characters

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
