# ADR 0028: Forbid All Implicit Configuration via Environment Variables

## Status

Accepted

## Date

2025-11-17

## Context

A need was identified to provide global configurations, such as ignore patterns, that apply to all library calls. The initial proposal was to use an environment variable like `ENVRESOLVE_IGNORE_PATTERNS`. This seemed particularly suitable for the library's target use case: applications (e.g., AI agents) run by non-developer end-users who can configure applications via environment variables but cannot modify source code.

This led to a broader discussion about the library's core philosophy, weighing end-user convenience against the principles of security, predictability, and developer control, as established in ADR-0024. The discussion considered whether the library itself should magically alter its behavior based on ambient environment variables, or if it should act solely as a predictable tool for developers.

## Decision

The library will **not** implement any mechanism for its behavior to be implicitly controlled by environment variables. This includes, but is not limited to:

- Setting ignore patterns.
- Automatically registering secret providers.

All configuration that affects the library's behavior must be passed explicitly through the library's public API (e.g., as parameters to functions like `load_env` or `resolve_os_environ`).

The responsibility for reading environment variables and using them to configure the library lies solely with the application developer.

## Rationale

- **Adherence to Core Principles**: This decision directly upholds the principle of "Fine-Grained Control" (ADR-0024) and the strategy for "Explicit Activation" of optional features (ADR-0025). It ensures the library has no "magic" or surprising side effects.
- **Security by Default**: This approach prevents unintended behavior like "surprise network calls" that could result from automatically registering a provider. The library's security posture is determined by explicit code, not by its environment, adhering to the principle of least surprise.
- **Developer Clarity and Predictability**: The application's behavior is determined entirely by the code that invokes the library, making it easier for developers to understand, debug, and review. There are no hidden behaviors.
- **Developer Empowerment**: While it does not directly empower the end-user via the library, it empowers the *developer* to choose exactly how, and if, they want to expose configuration options to their users. A developer wishing to support configuration via an environment variable can do so easily and explicitly:

  ```python
  # Application code
  import os
  import envresolve

  ignore_patterns_str = os.environ.get("MY_APP_IGNORE_PATTERNS", "")
  ignore_patterns = [p.strip() for p in ignore_patterns_str.split(",") if p.strip()]

  envresolve.resolve_os_environ(ignore_patterns=ignore_patterns)
  ```

## Implications

### Positive Implications

- The library has a clear, secure, and highly predictable configuration model.
- The philosophical stance on explicitness is unambiguous, providing clear guidance for future development.
- It avoids a class of hard-to-debug issues where application behavior changes due to "hidden" environment variables.

### Concerns

- This places the full burden on application developers to implement environment-variable-based configuration if they need it for their end-users.
- **Mitigation**: This is the intended design. The library's primary user is the developer, and its primary duty is to be a secure and predictable tool. The required boilerplate is minimal and ensures the developer's intent is explicit in their codebase.

## Alternatives

### Allow Global Configuration via Environment Variables

- **Description**: The initial proposal, where an environment variable like `ENVRESOLVE_IGNORE_PATTERNS` would be automatically read by the library to configure ignore patterns.
- **Reason for Rejection**: This was **rejected** because it introduces implicit behavior that conflicts with the core principles of security and explicitness (ADR-0024).

### Allow Automatic Provider Registration via Environment Variables

- **Description**: A further proposal where an environment variable could automatically register a secret provider (e.g., `ENVRESOLVE_AZURE_KEY_VAULT_ENABLED=true`).
- **Reason for Rejection**: This was also **rejected** for the same reasons, but with even stronger security implications due to the introduction of unintended network activity.

## Future Direction

This ADR serves as a strong precedent. Any future proposal to add implicit configuration or behavior based on environment variables should be weighed against the principles laid out here and is likely to be rejected.

## References

- ADR-0024: Core Design Principle of 'Fine-Grained Control'
- ADR-0025: Strategy for Optional Dependencies and Extensibility
