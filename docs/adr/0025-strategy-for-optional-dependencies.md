# ADR 0025: Strategy for Optional Dependencies and Extensibility

## Status

Accepted

## Date

2025-11-17

## Context

The library's core purpose is to resolve environment variables, but its power is enhanced by integrating with external secret providers (e.g., Azure Key Vault). These integrations often require heavy third-party dependencies. Forcing these dependencies on all users would bloat the installation for those who don't need the feature and could lead to dependency conflicts.

## Decision

We will adopt a formal strategy for features that rely on optional, heavy third-party libraries, based on Python's "extras" system.

1. **Packaging**: Optional dependencies will be defined as "extras" in `pyproject.toml` (e.g., `envresolve[azure]`).
2. **Implementation**: The core library will **not** have a hard dependency on optional libraries. Feature-specific modules will use lazy-loading via `importlib.import_module` to import the required libraries only when the feature is used, building upon the approach established in ADR-0014.
3. **Error Handling**: If a user attempts to use a feature without the necessary dependencies installed, the library will raise a helpful `ProviderRegistrationError` that clearly instructs the user on how to install the required extra (e.g., `pip install envresolve[azure]`).
4. **Explicit Activation**: Features requiring optional dependencies must be explicitly activated by the user (e.g., by calling `register_azure_kv_provider()`), in line with the "Fine-Grained Control" principle established in ADR-0024.

## Rationale

- **Keeps Core Lightweight**: Users who only need core variable expansion get a minimal, fast-to-install package.
- **Avoids "Dependency Hell"**: Reduces the chance of version conflicts for users.
- **Clear User Guidance**: The runtime error provides immediate, actionable feedback, improving the user experience.
- **Explicit is Better than Implicit**: Manual registration makes it clear that an optional, dependency-heavy component is being activated. This aligns with ADR-0024.

## Implications

### Positive Implications

- A lean default installation for the majority of users.
- A clear, scalable pattern for adding new integrations in the future.
- Improved project maintainability by isolating optional dependencies.

### Concerns

- **Increased User Friction for Optional Features**: Users of optional features have an extra step: installing the correct extra (e.g., `pip install envresolve[azure]`) and registering the provider.
- **Mitigation**: This friction is intentional and desirable, as it makes the choice to add heavy dependencies explicit. It will be managed through clear and prominent documentation for every feature that requires an extra. The runtime error message itself will also serve as a form of documentation.

## Alternatives

### Include All Dependencies by Default

- **Description**: Bundle all provider dependencies into the default installation.
- **Reason for Rejection**: Violates the principle of keeping the core library lean and imposes an unnecessary dependency burden on the majority of users.

### Separate Packages for Each Provider

- **Description**: Publish each provider as a separate, installable package (e.g., `envresolve-azure`).
- **Reason for Rejection**: Greatly increases maintenance overhead (more repositories, more packages to publish). It also fragments the ecosystem. The "extras" approach provides a superior balance of decoupling and maintainability for the current scale of the project.

## Future Direction

All new providers or features that introduce significant external dependencies must follow this pattern.

## References

- ADR-0009: Manual Provider Registration Pattern
- ADR-0014: Importlib Lazy Import
- ADR-0024: Core Design Principle of 'Fine-Grained Control'
- [Python Packaging User Guide: Writing your pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
