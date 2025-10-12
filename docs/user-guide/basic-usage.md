# Basic Usage

## Variable Expansion

envresolve supports variable expansion using `${VAR}` and `$VAR` syntax.

### Simple Variable Expansion

=== "${VAR} syntax"

    ```python
    from envresolve import expand_variables

    env = {"VAULT_NAME": "my-vault"}
    result = expand_variables("${VAULT_NAME}", env)

    print(result)  # Output: my-vault
    ```

=== "$VAR syntax"

    ```python
    from envresolve import expand_variables

    env = {"VAULT_NAME": "my-vault"}
    result = expand_variables("$VAULT_NAME", env)

    print(result)  # Output: my-vault
    ```

### Multiple Variables

You can reference multiple variables in a single string:

```python
from envresolve import expand_variables

env = {
    "VAULT_NAME": "my-vault",
    "SECRET_NAME": "db-password"
}
result = expand_variables("akv://${VAULT_NAME}/${SECRET_NAME}", env)

print(result)  # Output: akv://my-vault/db-password
```

### Nested Variable Expansion

Variables can reference other variables:

```python
from envresolve import expand_variables

env = {
    "ENVIRONMENT": "prod",
    "VAULT_NAME": "${ENVIRONMENT}-vault",
    "SECRET_URI": "akv://${VAULT_NAME}/api-key"
}
result = expand_variables(env["SECRET_URI"], env)

print(result)  # Output: akv://prod-vault/api-key
```

## Using Environment Variables

### With os.environ

Use `EnvExpander` to expand variables from the current environment:

```python
import os
from envresolve import EnvExpander

# Set environment variable
os.environ["VAULT_NAME"] = "production-vault"

expander = EnvExpander()
result = expander.expand("akv://${VAULT_NAME}/secret")

print(result)  # Output: akv://production-vault/secret
```

!!! note "Snapshot Behavior"
    `EnvExpander` takes a snapshot of `os.environ` at initialization time. Changes to environment variables after initialization won't be reflected.

### With .env Files

Use `DotEnvExpander` to expand variables from a `.env` file:

```python
from envresolve import DotEnvExpander

# Contents of .env:
# VAULT_NAME=my-company-vault
# DB_PASSWORD=akv://${VAULT_NAME}/db-password
# API_KEY=akv://${VAULT_NAME}/api-key

expander = DotEnvExpander(".env")
db_password_uri = expander.expand("${DB_PASSWORD}")
api_key_uri = expander.expand("${API_KEY}")

print(db_password_uri)  # Output: akv://my-company-vault/db-password
print(api_key_uri)      # Output: akv://my-company-vault/api-key
```

## Error Handling

### Circular Reference Detection

envresolve automatically detects circular references and raises a clear error:

```python
from envresolve import expand_variables
from envresolve.exceptions import CircularReferenceError

env = {
    "A": "${B}",
    "B": "${A}"
}

try:
    result = expand_variables(env["A"], env)
except CircularReferenceError as e:
    print(f"Error: {e}")
    # Error: Circular reference detected: B -> A -> B

    # Inspect the exact cycle if you need more detail
    print(e.chain)  # ['B', 'A', 'B']
```

### Missing Variable Error

If a referenced variable doesn't exist, `VariableNotFoundError` is raised:

```python
from envresolve import expand_variables
from envresolve.exceptions import VariableNotFoundError

env = {"A": "value"}

try:
    result = expand_variables("${MISSING}", env)
except VariableNotFoundError as e:
    print(f"Error: {e}")
    # Error: Variable 'MISSING' not found
```

## Advanced Use Cases

### Building Secret URIs Dynamically

```python
from envresolve import expand_variables

# Define vault and environment once
env = {
    "ENVIRONMENT": "production",
    "VAULT": "${ENVIRONMENT}-keyvault",

    # Define all secrets using the vault
    "DB_HOST_URI": "akv://${VAULT}/db-host",
    "DB_USER_URI": "akv://${VAULT}/db-user",
    "DB_PASS_URI": "akv://${VAULT}/db-password",
    "API_KEY_URI": "akv://${VAULT}/api-key",
}

# Expand each URI
for key in ["DB_HOST_URI", "DB_USER_URI", "DB_PASS_URI", "API_KEY_URI"]:
    expanded = expand_variables(env[key], env)
    print(f"{key}: {expanded}")

# Output:
# DB_HOST_URI: akv://production-keyvault/db-host
# DB_USER_URI: akv://production-keyvault/db-user
# DB_PASS_URI: akv://production-keyvault/db-password
# API_KEY_URI: akv://production-keyvault/api-key
```

### Plain Text Pass-Through

Text without variable references is returned unchanged:

```python
from envresolve import expand_variables

result = expand_variables("plain text with $100 price", {"VAR": "value"})
print(result)  # Output: plain text with $100 price
```

Note: A lone `$` followed by non-variable characters (like digits) is preserved.
