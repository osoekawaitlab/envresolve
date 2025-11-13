# Architecture Decision Record (ADR)

## Title

Use `importlib` for Lazy Optional Dependency Loading with Rich Errors

## Status

Accepted

## Date

2025-10-14

## Context

The Azure Key Vault provider depends on optional packages (`azure-identity`, `azure-keyvault-secrets`). Direct imports at module load time cause two problems:

1. Importing `envresolve.providers.azure_kv` raises `ModuleNotFoundError` in environments without the Azure SDK, even if Azure functionality is never used.
2. The resulting errors do not clearly instruct users which extras to install.

We need a pattern that defers importing optional dependencies until the provider is actually requested and that explains how to resolve missing dependencies.

## Decision

Use `importlib.import_module` inside `EnvResolver.register_azure_kv_provider` to load the provider lazily and produce a detailed error message when dependencies are missing.

```python
import importlib


def register_azure_kv_provider(self, **kwargs: Any) -> None:
    try:
        provider_module = importlib.import_module("envresolve.providers.azure_kv")
        provider_class = provider_module.AzureKVProvider
    except ImportError as exc:  # Missing provider module or downstream deps
        missing: list[str] = []
        try:
            importlib.util.find_spec("azure.identity")
        except (ImportError, ModuleNotFoundError):
            missing.append("azure-identity")

        try:
            importlib.util.find_spec("azure.keyvault.secrets")
        except (ImportError, ModuleNotFoundError):
            missing.append("azure-keyvault-secrets")

        if missing:
            hint = ", ".join(missing)
            raise ProviderRegistrationError(
                f"Azure Key Vault provider requires {hint}. "
                "Install with `pip install envresolve[azure]`.",
                original_error=exc
            ) from exc

        raise ProviderRegistrationError(
            "Failed to import Azure Key Vault provider; see chained exception for details.",
            original_error=exc
        ) from exc

    provider = provider_class(**kwargs)
    self._providers["akv"] = provider
```

## Rationale

- **Lazy optional dependencies**: Users without Azure extras can still import the package and use non-Azure features (aligns with ADR-0012).
- **Actionable errors**: When dependencies are missing, the raised message explicitly lists the missing packages and the extras command to install.
- **Custom exception hierarchy**: Uses `ProviderRegistrationError` instead of `ImportError` to align with ADR-0002 (custom exception hierarchy).
- **Style compliance**: Avoids Ruff's unused-import warnings and removes the need for `noqa` comments.
- **Extensibility**: Same pattern can be reused for future optional providers.

## Implications

### Positive Implications

- Importing `envresolve` no longer requires the Azure SDK.
- Developers receive clear instructions on how to enable Azure functionality.
- Custom exception allows clients to handle provider registration errors separately from other errors (catch `ProviderRegistrationError` specifically or all envresolve errors via `EnvResolveError`).
- Unit tests can patch `importlib.import_module` to simulate missing dependencies.

### Concerns

- **Slightly more boilerplate**: Lazy import logic is longer than a simple `try/except ImportError`. *Mitigation*: Isolated inside a helper method and well-documented.
- **Runtime detection cost**: Uses `importlib.util.find_spec` to check dependencies. *Mitigation*: Called only when the provider is registered, not on every secret resolution.

## Alternatives

### Traditional `try/except` around Direct Import

- **Pros**: Very concise.
- **Cons**: Cannot distinguish which dependency is missing; forces import at module load time.
- **Rejection reason**: Fails the usability goal of actionable diagnostics and prevents import without Azure SDK.

### `TYPE_CHECKING` Guards

- **Pros**: Keeps type checkers aware of symbols while skipping runtime import.
- **Cons**: Does not help when the provider is actually used at runtime; still fails once the guarded code executes.
- **Rejection reason**: Insufficient for runtime optionality.

### Entry-Point Based Discovery

- **Pros**: Can lazily load providers via plugin mechanism.
- **Cons**: Overkill for first-party providers and shifts complexity to packaging.
- **Rejection reason**: Simpler explicit import is adequate.

## Future Direction

- Extract repeated dependency-check logic into a reusable helper once additional providers are added.
- Log missing-dependency diagnostics at DEBUG level when running in verbose mode to aid support investigations.
- Combine with ADR-0012 to remove explicit `--ignore` flags once all optional modules load lazily.

## References

- Implementation: `src/envresolve/api.py::EnvResolver.register_azure_kv_provider`
- Related ADRs: 0002 (custom exception hierarchy), 0009 (provider registry), 0012 (pytest markers for optional providers)
- Python docs: <https://docs.python.org/3/library/importlib.html>
- Issue #5: Changed from `ImportError` to `ProviderRegistrationError` to align with ADR-0002
