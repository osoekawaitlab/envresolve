# Architecture Decision Record (ADR)

## Title

Encapsulate Resolution State in `EnvResolver` Class with Module Facade

## Status

Accepted

## Date

2025-10-14

## Context

Early iterations of the secret resolution API maintained provider registrations and resolver state in module-level globals (`_PROVIDERS`, `_RESOLVER`). Although simple, this approach leaked mutable global state, required `global` declarations when mutating, and made it difficult to instantiate isolated resolvers for tests or advanced scenarios.

We needed a structure that:

- Removes direct `global` manipulation from public functions
- Keeps the existing top-level API (`envresolve.resolve_secret`, `load_env`) for backward compatibility
- Allows creation of multiple resolver instances for specialized use cases (e.g., custom registries in tests)
- Keeps the provider registration pattern defined in ADR-0009

## Decision

Introduce an `EnvResolver` class that encapsulates provider registration and resolution logic, and expose a singleton instance through module-level facade functions.

```python
class EnvResolver:
    def __init__(self) -> None:
        self._providers: dict[str, SecretProvider] = {}
        self._resolver: SecretResolver | None = None

    def register_azure_kv_provider(self, **kwargs: Any) -> None:
        ...

    def resolve_secret(self, uri: str) -> str:
        ...

    def load_env(self, path: PathLike[str] | None = None) -> dict[str, str]:
        ...


_DEFAULT_RESOLVER = EnvResolver()


def resolve_secret(uri: str) -> str:
    return _DEFAULT_RESOLVER.resolve_secret(uri)


def register_azure_kv_provider(**kwargs: Any) -> None:
    _DEFAULT_RESOLVER.register_azure_kv_provider(**kwargs)
```

## Rationale

- **Encapsulation**: All mutable state (providers, cached resolver) is confined to an instance, eliminating `global` mutation patterns.
- **Testability**: Tests can instantiate `EnvResolver()` directly, register mock providers, and assert behavior without touching the global singleton.
- **Extensibility**: Future features (per-resolver caches, alternative registries) can build on the class without breaking the public facade.
- **Backward compatibility**: Existing users continue to call module-level functions; no API breakage.

## Implications

### Positive Implications

- Cleaner separation between public facade and implementation details.
- Multiple resolvers can coexist in the same process if needed (e.g., multi-tenant scenarios).
- Easier to reason about initialization order—`EnvResolver` constructor localizes default setup.

### Concerns

- **Slightly higher indirection**: Developers must look inside the class to understand state transitions. *Mitigation*: Comprehensive docstrings and ADR references.
- **Singleton management**: The `_DEFAULT_RESOLVER` remains module-level global state. *Mitigation*: Singleton usage isolated to facade; alternative resolvers supported when required.

## Alternatives

### Keep Module-Level Globals

- **Pros**: Minimal code; fewer indirections.
- **Cons**: `global` keyword required for updates; difficult to create isolated resolver instances; tightly couples API to implementation details.
- **Rejection reason**: Conflicts with encapsulation and testability goals.

### Dependency Injection via Function Parameters

- **Pros**: Explicitly pass provider registry/resolver to every function.
- **Cons**: Verbose public API; callers must thread dependencies through each call; hurts ergonomics.
- **Rejection reason**: Overly burdensome for primary use cases; the facade pattern strikes a better balance.

### Metaclass-Based Singleton

- **Pros**: Guarantees only one instance ever exists.
- **Cons**: Unnecessarily complex; prevents intentional multiple instances in tests.
- **Rejection reason**: Simpler explicit singleton (module-level instance) suffices.

## Future Direction

- Provide factory helpers (e.g., `create_resolver()`) that pre-register common providers.
- Expose hooks for dependency injection (custom cache, custom secret resolver) during `EnvResolver` initialization.
- Evaluate whether the `_DEFAULT_RESOLVER` should be lazy-initialized to reduce import-time side effects once provider registrations grow.

## References

- Implementation: `src/envresolve/api.py`
- Tests: `tests/unit/test_resolver.py`, `tests/e2e/test_nested_resolution.py`
- Related ADRs: 0009 (manual provider registration), 0010 (iterative URI resolution), 0014 (lazy imports for optional providers)
