# Roadmap

## Current Version: 0.1.7

### Completed Features

- ✅ Variable expansion with `${VAR}` and `$VAR` syntax
- ✅ Circular reference detection
- ✅ Nested variable expansion
- ✅ Support for `os.environ`, `.env` files, and custom dictionaries
- ✅ Secret URI resolution with Azure Key Vault provider (`resolve_secret`, `load_env`)
- ✅ Variable ignore patterns (Phase 1): `ignore_keys` parameter for exact string matching

## Planned Features

### v0.1.x (In Progress)

- Structured logging hooks for resolution diagnostics
- Variable ignore patterns (Phase 2 & 3):
    - ✅ Phase 1: `ignore_keys` parameter with exact string matching
    - Phase 2: `ignore_patterns` parameter with glob-style matching (e.g., `PS*`, `PROMPT*`)
    - Phase 3: `ENVRESOLVE_IGNORE` environment variable configuration

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
