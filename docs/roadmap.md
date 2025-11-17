# Roadmap

## Current Version: 0.1.9

### Completed Features

- ✅ Variable expansion with `${VAR}` and `$VAR` syntax
- ✅ Circular reference detection
- ✅ Nested variable expansion
- ✅ Support for `os.environ`, `.env` files, and custom dictionaries
- ✅ Secret URI resolution with Azure Key Vault provider (`resolve_secret`, `load_env`)
- ✅ Error context with `EnvironmentVariableResolutionError` wrapper (v0.1.8)
- ✅ Variable ignore patterns (Phase 1 & 2):
    - Phase 1: `ignore_keys` parameter for exact string matching
    - Phase 2: `ignore_patterns` parameter with glob matching (`*`, `?`, `[seq]`)

## Planned Features

### v0.1.x (In Progress)

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

### Rejected Features

- ❌ Variable ignore patterns (Phase 3): `ENVRESOLVE_IGNORE_PATTERNS` environment variable
    - **Reason**: Violates core design principle of explicit configuration (ADR-0028)
    - **Alternative**: Application developers can read env vars and pass to API parameters
    - See ADR-0028 for detailed rationale
