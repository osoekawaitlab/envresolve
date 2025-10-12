# envresolve

**envresolve** is a Python library for resolving environment variables from secret stores (e.g., Azure Key Vault).

## Features

- **Variable Expansion**: Support for `${VAR}` and `$VAR` syntax with nested expansion
- **Circular Reference Detection**: Automatically detects and prevents circular variable references
- **Multiple Sources**: Works with `os.environ`, `.env` files, or custom dictionaries
- **Type Safe**: Built with strict type checking using mypy
- **Well Tested**: 100% test coverage with comprehensive unit and E2E tests

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
