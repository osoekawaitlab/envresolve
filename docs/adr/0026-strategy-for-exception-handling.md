# ADR 0026: Strategy for Exception Handling and Error Reporting

## Status

Accepted

## Date

2025-11-17

## Context

The library interacts with multiple external systems (environment, filesystem, secret providers) and performs complex internal operations (variable parsing, reference resolution). A consistent, predictable, and informative error handling strategy is crucial for user trust and ease of debugging. Errors must be easy to handle programmatically and provide clear, actionable context about the failure.

## Decision

We will adopt a unified strategy for exception handling and error reporting, based on three core tenets:

1. **Custom Hierarchy**: All exceptions raised directly by the library will inherit from a single base exception, `EnvResolveError`. This allows users to reliably catch any library-specific error with a single `except EnvResolveError:` block. This was established in ADR-0002.
2. **Granular Types**: Specific, distinct error conditions (e.g., a circular reference, an invalid URI, a provider configuration issue) will have their own exception types inheriting from the base class. This enables fine-grained, programmatic error handling for advanced use cases. This pattern was established in ADR-0003, ADR-0016, and ADR-0018.
3. **Contextual Wrapping**: When a low-level exception occurs during a high-level operation (e.g., a `KeyError` from a provider during the resolution of `MY_VAR`), it will be caught and "wrapped." A new, higher-level exception will be raised that provides context about the operation that failed (e.g., "Failed to resolve MY_VAR") and chains the original exception (`__cause__`) for full traceability and debugging. This was established in ADR-0021.

## Rationale

- **Usability**: The single base exception makes it simple for users to implement basic, robust error handling for all library-related issues.
- **Programmability**: Granular exception types allow advanced users to build conditional logic based on specific failure modes (e.g., retry on a network error, halt on a configuration error).
- **Debuggability**: Exception wrapping and chaining provide a full stack trace with context at each level of the call stack, making it much easier to diagnose the root cause of a problem.

## Implications

### Positive Implications

- Users receive a consistent, powerful, and predictable error handling API.
- Library developers have a clear, established pattern to follow when adding new features and error conditions.
- The library's behavior becomes more transparent and easier to troubleshoot.

### Concerns

- **Proliferation of Exception Classes**: This strategy could lead to a large number of custom exception classes.
- **Mitigation**: A new exception type should only be introduced for a genuinely distinct error condition that a user might reasonably want to handle differently programmatically. Trivial variations should not get new classes.

## Alternatives

### Using Standard Python Exceptions

- **Description**: Directly raise built-in exceptions like `ValueError`, `KeyError`, etc.
- **Reason for Rejection**: This makes it impossible for users to distinguish between errors raised intentionally by the `envresolve` library and those raised by other parts of their application or Python's standard library. It breaks the promise of a reliable error handling API.

### Error Codes with a Single Exception Type

- **Description**: Use one generic `EnvResolveError` and pass different error codes or messages to distinguish failure modes.
- **Reason for Rejection**: This is not an idiomatic Python practice. Using distinct exception classes is the standard, preferred way to represent different error conditions, as it works better with Python's `try...except` mechanism and provides better support for static analysis and IDEs.

## Future Direction

All new error conditions added to the library must conform to this three-part strategy.

## References

This ADR formalizes the strategy established across the following decisions:

- ADR-0002: Custom Exception Hierarchy
- ADR-0003: Structured Exception Design
- ADR-0016: TypeError-based Custom Exception for Mutually Exclusive Parameters
- ADR-0018: Granular Error Handling for Variable Expansion and Secret Resolution
- ADR-0021: Exception Wrapping for Variable Resolution Context
