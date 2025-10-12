# envresolve
Resolve env vars from secret stores.

## Quick start

```python
from envresolve import expand_variables

env = {"VAULT": "corp-kv", "SECRET": "db-password"}
print(expand_variables("akv://${VAULT}/${SECRET}", env))
# akv://corp-kv/db-password
```

More examples and API details: https://osoekawaitlab.github.io/envresolve/
