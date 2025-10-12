# Installation

## Requirements

- Python 3.9 or higher

## Install from PyPI

```bash
pip install envresolve
```

## Install with uv

```bash
uv pip install envresolve
```

## Install for Development

To install envresolve for development with all dependencies:

```bash
# Clone the repository
git clone https://github.com/osoekawaitlab/envresolve.git
cd envresolve

# Install with development dependencies
uv sync

# Run tests
nox -s tests

# Run all quality checks
nox -s check_all
```

## Optional Dependencies

### Azure Key Vault Support (Coming Soon)

```bash
pip install envresolve[azure]
```

This installs:

- `azure-identity`
- `azure-keyvault-secrets`

## Verify Installation

```python
import envresolve
print(envresolve.__version__)
```

Expected output: `0.1.0`
