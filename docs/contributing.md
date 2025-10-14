# Contributing to envresolve

Thank you for considering contributing to envresolve!

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Setup

1. Fork and clone the repository:

```bash
git clone https://github.com/osoekawaitlab/envresolve.git
cd envresolve
```

1. Install dependencies:

```bash
uv sync
```

1. Run tests to verify setup:

```bash
nox -s tests
```

## Development Workflow

envresolve follows a strict Test-Driven Development (TDD) cycle.

### Running Tests

```bash
# All tests with coverage
nox -s tests

# Unit tests only
nox -s tests_unit

# E2E tests only
nox -s tests_e2e

# All Python versions
nox -s tests_all_versions
```

### Code Quality

```bash
# Type checking
nox -s mypy

# Linting
nox -s lint

# Format code
nox -s format_code

# All quality checks
nox -s quality

# Everything (tests + quality)
nox -s check_all
```

## Code Style

- **Type Hints**: Required for all public APIs
- **Docstrings**: Google style, required for all public functions/classes
- **Linting**: Ruff with "ALL" rules (see `pyproject.toml`)
- **Type Checking**: Strict mypy configuration

## Pull Request Process

1. Create a new branch from `main`
2. Make your changes following the TDD cycle
3. Ensure all tests pass: `nox -s check_all`
4. Update documentation if needed
5. Write or update ADRs for architectural decisions
6. Submit a pull request with a clear description

### PR Checklist

- [ ] Tests added/updated and passing
- [ ] Code follows style guidelines (ruff check passes)
- [ ] Type hints added (mypy passes)
- [ ] Docstrings added/updated (Google style)
- [ ] Coverage maintained at 80%+
- [ ] ADRs written for design decisions
- [ ] Documentation updated if needed

## Architecture

envresolve follows a layered architecture:

```
Layer 5: api.py (Public API facade)
Layer 4: application/ (resolver, cache)
Layer 3: providers/ (factory, registry, implementations)
Layer 2: services/ (reference, expansion)
Layer 1: Domain (models, exceptions) + Infrastructure (base, logging)
Layer 0: External dependencies
```

**Key Principles**:

- Higher layers depend on lower layers
- Lower layers NEVER depend on higher layers
- Domain layer has NO internal dependencies

See [Architecture ADRs](architecture/adr.md) for design decisions.

## Documentation

Documentation is built with MkDocs Material:

```bash
# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

### Documentation Structure

- **User Guide**: Installation and usage tutorials
- **API Reference**: Auto-generated from docstrings (mkdocstrings)
- **Architecture**: ADRs and design decisions
- **Contributing**: This file

## Reporting Issues

Use the [GitHub issue tracker](https://github.com/osoekawaitlab/envresolve/issues) to report bugs or request features.

When reporting bugs, please include:

- Python version
- envresolve version
- Minimal code to reproduce
- Expected vs actual behavior
- Error messages/stack traces

## Questions?

- Check the [documentation](https://osoekawaitlab.github.io/envresolve)
- Review [existing issues](https://github.com/osoekawaitlab/envresolve/issues)
- Open a new issue for questions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Live Azure Tests

Optional integration tests against real Azure Key Vault infrastructure. Run these tests to validate changes that affect Azure SDK integration or provider implementations.

**Note**: Live tests automatically skip when environment variables are not set (`ENVRESOLVE_LIVE_KEY_VAULT_NAME`, etc.), so they won't interfere with normal development.

### One-Time Setup

```bash
# 1. Configure terraform (requires Azure subscription and az login)
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars

# 2. Edit terraform.tfvars with your values:
#    - subscription_id, tenant_id, name_prefix
#    - test_principal_object_id (get your object ID: az ad signed-in-user show --query id -o tsv)

# 3. Create resources
terraform init
terraform apply

# 4. Return to project root and set environment variables (per shell session)
cd ../..
source scripts/setup_live_tests.sh
```

### Running Live Tests

```bash
nox -s tests_live
```

### Cleanup

Resources can be kept for reuse. Destroy only when done:

```bash
cd infra/terraform
terraform destroy
```
