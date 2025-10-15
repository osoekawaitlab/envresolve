# Installation

## Requirements

- Python 3.10 or higher

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

### Azure Key Vault Support

Install the Azure extra when you need `akv://` resolution:

```bash
pip install envresolve[azure]
```

This pulls in:

- `azure-identity`
- `azure-keyvault-secrets`

After installation, register the provider before resolving secrets:

```python
import envresolve

envresolve.register_azure_kv_provider()
```
