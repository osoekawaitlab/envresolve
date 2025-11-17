# ADR 0027: API Design for State Management (Class-Based Core with Default Instance Facade)

## Status

Accepted

## Date

2025-11-17

## Context

The library's core functionality involves managing configuration state, such as registered secret providers, their settings, and resolution caches. The API design must address how this state is managed and exposed to users. A purely function-based API requiring explicit state passing can be verbose and cumbersome. Conversely, a purely class-based API offers excellent encapsulation but can introduce boilerplate for simple use cases.

## Decision

We will adopt a hybrid API design that serves both simple and advanced use cases, formalizing the evolution from ADR-0004 to ADR-0013.

1. **Stateful Core (`EnvResolver` Class)**: The primary, state-holding component is the `EnvResolver` class. It encapsulates all configuration (e.g., the provider registry) and exposes methods for resolution (`resolve_secret`, `load_env`, `resolve_os_environ`). This class is the core API for advanced, repeated, or isolated use cases (e.g., in testing).
2. **Default Instance Facade (Module-Level Functions)**: For convenience and simple use cases, we will provide module-level facade functions (`envresolve.resolve_secret`, `envresolve.load_env`, `envresolve.resolve_os_environ`). These functions will operate on a default, shared instance of `EnvResolver` (stored as a module-level variable `_default_resolver`) that is instantiated at import time.

## Rationale

- **Flexibility for Power Users**: The stateful `EnvResolver` class offers power, encapsulation, and testability. Advanced users can create multiple, isolated resolver instances with different configurations.
- **Simplicity for Beginners**: The default instance facade provides a simple, zero-setup entry point for users with basic needs, significantly lowering the barrier to entry. This allows for a "drop-in replacement" experience for tools like `python-dotenv`.
- **Clear Separation of Concerns**: This hybrid model clearly separates the one-time action of *resolution* from the persistent state of *configuration*.
- **Shared State Benefits**: The default instance allows state (such as registered providers) to be shared across multiple function calls, avoiding redundant provider registration.

## Implications

### Positive Implications

- The library is approachable for beginners while remaining powerful and flexible for experts.
- The design is highly test-friendly, as `EnvResolver` instances can be created and configured on-the-fly within tests without affecting the default global instance.
- It provides a clear path for users to graduate from simple to advanced usage.
- Module-level functions share a single default instance, avoiding redundant provider registrations.

### Concerns

- **Dual APIs**: The existence of two ways to perform actions (instance methods vs. module functions) could potentially confuse some users.
- **Mitigation**: The documentation must clearly explain the two approaches and provide guidance on when to use each. The recommendation will be: "Start with the simple module functions; use the `EnvResolver` class when you need to customize configuration, manage multiple configurations, or for better test isolation."
- **Global State**: The default instance is shared across the application, which means provider registrations affect all subsequent calls to module-level functions.
- **Mitigation**: This is the intended behavior for most use cases. Users who need isolation can create their own `EnvResolver` instances.

## Alternatives

### Purely Function-Based API with Explicit State Passing

- **Description**: Only provide functions that accept all configuration as arguments on every call (e.g., `resolve(value, providers=...)`).
- **Reason for Rejection**: This was the initial approach (ADR-0004) but was found to be extremely verbose and cumbersome for any use case involving a configured provider. It does not allow for a persistent, configured "resolver" object.

### Purely Stateful API

- **Description**: Only provide the `EnvResolver` class and require users to instantiate it for all operations.
- **Reason for Rejection**: This adds boilerplate and friction for simple, one-off use cases (e.g., resolving a single dictionary). It would harm the library's approachability and prevent it from serving as a simple, drop-in tool.

## Future Direction

This hybrid pattern of a stateful core class with a default instance facade should be maintained. New functionality should be implemented as methods on `EnvResolver` first, and then exposed as a module-level facade if it serves a common, simple use case.

## References

- ADR-0004: Stateless Function-Based Variable Expansion (Initial approach)
- ADR-0013: Class-Based API Design (Superseding decision establishing the class-based core)
