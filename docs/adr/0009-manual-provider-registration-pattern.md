# Architecture Decision Record (ADR)

## Title

Use Manual Provider Registration with Global Registry

## Status

Accepted

## Date

2025-10-13

## Context

The Azure Key Vault secret resolution feature (Issue #3) required a mechanism to integrate secret providers with the resolution system. Several architectural questions arose:

1. How should providers be discovered and registered?
2. Should provider registration be automatic or explicit?
3. How should the provider registry be structured?
4. Should providers be singletons or instantiated per use?

Key constraints:

- Users may not need all provider types (e.g., only Azure, not AWS)
- Provider initialization may require credentials or configuration
- Library should support multiple secret backends (Azure KV, AWS Secrets Manager, etc.)
- API should be simple and discoverable

## Decision

Use **manual provider registration with a global registry**:

1. **Manual registration**: Users explicitly call `register_azure_kv_provider()` before resolving secrets
2. **Global registry**: Module-level `_PROVIDERS` dict maps URI schemes to provider instances
3. **Singleton providers**: One provider instance per scheme, reused across all resolutions
4. **Explicit API**: Registration functions are top-level exports (e.g., `envresolve.register_azure_kv_provider()`)

**Implementation pattern:**

```python
# api.py
_PROVIDERS: dict[str, SecretProvider] = {}

def register_azure_kv_provider() -> None:
    """Register Azure Key Vault provider for akv:// and kv:// schemes."""
    provider = AzureKVProvider()
    _PROVIDERS["akv"] = provider
    _PROVIDERS["kv"] = provider  # Alias

def _get_provider(scheme: str) -> SecretProvider:
    """Get provider for scheme, raise if not registered."""
    if scheme not in _PROVIDERS:
        raise SecretResolutionError(f"No provider registered for scheme '{scheme}'")
    return _PROVIDERS[scheme]
```

## Rationale

**Why manual registration?**

- **Opt-in dependencies**: Users only install and register providers they need
- **Explicit control**: Clear when providers are initialized (e.g., after credential setup)
- **No magic**: Obvious what's happening, easier to debug
- **Configuration flexibility**: Can pass custom credentials or config during registration

**Why global registry?**

- **Simplicity**: No need to pass registry through call chains
- **Singleton benefits**: Provider instances can cache connections (e.g., Azure SecretClient per vault)
- **Idempotent registration**: Safe to call `register_*()` multiple times
- **Thread-safe for reads**: Once registered, providers are read-only

**Why singleton providers?**

- **Resource efficiency**: Reuse authenticated clients across resolutions
- **Connection pooling**: Provider maintains connection cache internally
- **Stateless operations**: `resolve()` method is stateless, safe to share

## Implications

### Positive Implications

- **Clear API surface**: `register_*()` functions are discoverable via autocomplete
- **Lazy loading**: Only imported providers are loaded (no startup overhead)
- **Testability**: Easy to mock providers by registering test implementations
- **Extensibility**: New providers follow same pattern (e.g., `register_aws_provider()`)
- **Error messages**: Clear "provider not registered" errors guide users

### Concerns

- **Manual setup required**: Users must remember to call `register_*()` before use
    - Mitigation: Clear error messages with registration instructions
    - Mitigation: Examples in documentation show registration as first step

- **Global state**: Module-level registry is mutable global state
    - Mitigation: Registration is write-once in typical usage
    - Mitigation: Tests can clear registry between test cases if needed
    - Future: Consider making registry explicit parameter for advanced use cases

- **No auto-discovery**: Cannot scan for available providers automatically
    - Mitigation: Explicit is better than implicit (Zen of Python)
    - Future: Optional `register_all()` for convenience if many providers exist

## Alternatives

### Auto-Registration via Import

Automatically register providers when modules are imported:

```python
# providers/azure_kv.py
# Auto-registers on import
from envresolve.api import _PROVIDERS
_PROVIDERS["akv"] = AzureKVProvider()
```

- **Pros**: No manual registration needed, automatic discovery
- **Cons**:
    - Imports have side effects (anti-pattern)
    - Cannot control initialization timing
    - Cannot pass configuration
    - Harder to test (import side effects)
    - Forces loading of all provider dependencies
- **Rejection reason**: Side effects on import violate Python best practices; explicit is better

### Registry as Explicit Parameter

Pass registry explicitly through function calls:

```python
registry = ProviderRegistry()
registry.register("akv", AzureKVProvider())
result = resolve_secret("akv://...", registry=registry)
```

- **Pros**:
    - No global state
    - Easy to use multiple registries
    - Explicit dependency injection
- **Cons**:
    - Verbose - every call needs registry parameter
    - Poor ergonomics for simple use cases
    - Complicates API significantly
- **Rejection reason**: Over-engineered for typical use; global registry is simpler

### Plugin System with Entry Points

Use setuptools entry points for automatic discovery:

```python
# setup.py
entry_points={
    "envresolve.providers": [
        "akv = envresolve.providers.azure_kv:AzureKVProvider"
    ]
}
```

- **Pros**:
    - Standard Python plugin pattern
    - Extensible by third-party packages
    - Auto-discovery without imports
- **Cons**:
    - Overkill for first-party providers
    - Complexity in initialization and configuration
    - Harder to debug
    - Not needed until third-party provider ecosystem exists
- **Rejection reason**: Premature optimization; manual registration is sufficient for v0.1.x

### Factory Pattern with Builder

Use factory pattern for provider creation:

```python
provider = ProviderFactory.create("azure_kv", vault="my-vault")
result = resolve_secret("akv://...", provider=provider)
```

- **Pros**:
    - Flexible provider configuration
    - No global state
- **Cons**:
    - Users must manage provider lifecycle
    - Verbose for simple cases
    - Cannot share providers across resolutions
- **Rejection reason**: Too much manual management; global registry with caching is better

## Future Direction

- **Optional `register_all()` convenience**: If many providers exist, provide single-call registration:

  ```python
  envresolve.register_all()  # Registers all installed providers
  ```

- **Registry introspection**: Add query functions if needed:

  ```python
  envresolve.list_providers()  # → ["akv", "kv", "aws"]
  envresolve.is_provider_registered("akv")  # → bool
  ```

- **Thread-safe registry mutations**: If use cases emerge for dynamic provider registration in threaded environments, add locking

- **Custom registries for advanced use cases**: Support optional explicit registry parameter:

  ```python
  custom_registry = ProviderRegistry()
  resolve_secret("akv://...", registry=custom_registry)  # Override global
  ```

- **Provider configuration API**: If providers need complex configuration, add builder pattern:

  ```python
  register_azure_kv_provider(
      credential=my_credential,
      cache_ttl=600,
      retry_policy=my_policy
  )
  ```

## References

- Issue #3: Azure Key Vault secret resolution support
- Implementation: `src/envresolve/api.py` (registry and registration functions)
- Implementation: `src/envresolve/providers/azure_kv.py` (provider implementation)
- Python Zen: "Explicit is better than implicit"
- Python anti-patterns: Import-time side effects
