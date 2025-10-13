# envresolve
Resolve env vars from secret stores.

## Quick start

```python
from envresolve import expand_variables

env = {"VAULT": "corp-kv", "SECRET": "db-password"}
print(expand_variables("akv://${VAULT}/${SECRET}", env))
# akv://corp-kv/db-password
```

Secret resolution with Azure Key Vault:

```python
import envresolve

envresolve.register_azure_kv_provider()  # requires `pip install envresolve[azure]`
print(envresolve.resolve_secret("akv://corp-vault/db-password"))
```

More examples and API details: https://osoekawaitlab.github.io/envresolve/
