# ADR 0024: Core Design Principle of 'Fine-Grained Control'

## Status

Accepted

## Date

2025-11-17

## Context

This library is designed to serve a wide range of scenarios, from simple environment variable expansion to complex, multi-provider secret resolution. In such a diverse landscape, implicit or "magical" behaviors can lead to user confusion, unpredictable outcomes, and security risks, especially when handling sensitive data. Users must be able to understand, predict, and explicitly manage how the library behaves in their specific environment.

## Decision

We will adopt **"Fine-Grained Control"** as a core design principle for all API and feature development.

This principle dictates that we should:

1. **Prioritize explicit configuration over implicit conventions.**
2. **Provide clear mechanisms for users to override or extend default behaviors.**
3. **Ensure the library's actions are transparent and easy to reason about.**

## Rationale

- **Predictability**: Explicit configuration makes the library's behavior deterministic and easier for users to understand, reducing unexpected side effects.
- **Flexibility**: It empowers users to adapt the library for complex or non-standard requirements without "fighting the framework."
- **Security**: When dealing with secrets, explicit control is paramount. It minimizes the risk of accidental secret exposure through unforeseen or magical behavior.
- **Maintainability**: APIs that are explicit and clear are easier to evolve and maintain over the long term, often with fewer breaking changes.

## Implications

### Positive Implications

- **Increased User Trust**: Users will have more confidence in a library that behaves predictably.
- **Enhanced Robustness**: Applications built with this library will be more robust as their configuration is explicit.
- **Easier Debugging**: When issues arise, the cause is more likely to be found in explicit configuration rather than hidden, implicit behavior.
- **Clear Guidance**: This principle will serve as a clear guide for future API design and contribution discussions.

### Concerns

- **API Verbosity**: A commitment to this principle can lead to more verbose APIs compared to "convention over configuration" frameworks.
- **Mitigation**: We will mitigate this by providing sensible defaults and creating simple, stateless facade functions (e.g., `resolve_os_environ`) for the most common use cases, offering a simpler entry point without sacrificing underlying control.

## Alternatives

### Convention over Configuration

- **Description**: A design paradigm where the framework makes numerous assumptions to reduce boilerplate code for standard use cases.
- **Pros**: Can make common tasks very quick and simple.
- **Cons**: Can be opaque, difficult to debug, and inflexible when requirements deviate from the convention.
- **Reason for Rejection**: The domain of environment and secret management is too sensitive and varied for a one-size-fits-all set of conventions. The risk of unexpected behavior with secrets outweighs the benefit of reduced boilerplate.

## Future Direction

This ADR should be referenced in future architectural decisions as a primary justification for design choices that favor explicitness and user control.

## References

This principle is exemplified in the following decisions:

- ADR-0009: Manual Provider Registration Pattern
- ADR-0018: Granular Error Handling for Variable Expansion and Secret Resolution
