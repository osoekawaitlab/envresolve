# ADR 0029: Logger Propagation Through Layers

## Status

Accepted

## Date

2025-11-25

## Context

The library needs to support optional logging for diagnostic purposes. Users should be able to:

1. Configure a logger at the `EnvResolver` instance level via constructor
2. Set a global default logger via `set_logger()` for module-level facade functions
3. Override the logger on a per-call basis via method parameters

The implementation must be thread-safe. If multiple threads call methods with different logger overrides simultaneously, they should not interfere with each other's logging behavior.

## Decision

Logger instances will be passed explicitly as parameters through all layers of the resolution stack, rather than mutating instance state.

**API Layer:**

```python
def resolve_secret(self, uri: str, logger: logging.Logger | None = None) -> str:
    effective_logger = logger if logger is not None else self._logger
    resolver = self._get_resolver()
    return resolver.resolve(uri, logger=effective_logger)
```

**Application Layer (`SecretResolver`):**

```python
def resolve(self, value: str, logger: logging.Logger | None = None) -> str:
    # Use logger for diagnostic messages
    # Pass logger to provider.resolve() if needed
```

**Provider Layer (`SecretProvider`):**

```python
def resolve(self, parsed_uri: ParsedURI, logger: logging.Logger | None = None) -> str:
    # Use logger for diagnostic messages
```

**Note**: The `SecretProvider` protocol is part of the public API, as users can implement custom providers. This signature change is a breaking change for custom provider implementations.

## Rationale

- **Thread Safety**: Passing logger as a parameter eliminates shared mutable state, making the implementation inherently thread-safe
- **Explicit and Traceable**: The logger's path through the system is explicit in method signatures, making it easy to understand and debug
- **Simple Design**: This approach is straightforward without introducing new abstractions like context objects
- **Acceptable Breaking Change**: While `SecretProvider` is a public protocol, the library is in 0.x version where breaking changes are acceptable. Custom provider implementations will need to add the `logger` parameter, but this is a straightforward migration

## Implications

### Positive Implications

- Thread-safe logger override behavior
- Clear, explicit control flow for logger propagation
- Easy to test and debug
- No risk of logger state leaking between concurrent calls
- Follows common Python patterns for passing context through call stacks

### Concerns

- **Breaking Change for Custom Providers**: Users who have implemented custom `SecretProvider` classes will need to update their `resolve()` method signature to include the `logger` parameter
- **Mitigation**: The library is in 0.x version where breaking changes are expected. Migration is straightforward: add `logger: logging.Logger | None = None` parameter. This will be clearly documented in release notes and migration guide.

- **Parameter Passing Overhead**: Logger parameter must be passed through each layer
- **Mitigation**: The overhead is minimal, and the explicitness improves code clarity

- **Less Flexibility for Future Context**: If we need to add more context parameters in the future (e.g., request ID, timeout), we'll have to either add more parameters or refactor to a context object, which would be another breaking change
- **Mitigation**: Accept this trade-off. The library is in 0.x, so future breaking changes are acceptable if needed. The current simple design is appropriate for present requirements.

## Alternatives

### Threading Local Storage

- **Description**: Use `threading.local()` to store the logger override implicitly
- **Pros**: No signature changes required; thread-safe
- **Cons**: Implicit state management makes debugging difficult; goes against Python best practices; harder to test
- **Reason for Rejection**: Implicit state is harder to reason about and debug, especially in a library context where users may have complex threading scenarios

### Context Object

- **Description**: Introduce a `ResolverContext` dataclass containing logger and future context information
- **Pros**: Thread-safe; extensible for future context data; keeps parameter count low; single breaking change if more context is needed later
- **Cons**: Introduces new abstraction when only logger is currently needed; over-engineering for present requirements
- **Reason for Rejection**: While this would make future extensions easier, it's premature abstraction. The current requirement is only for logger propagation. However, note that if additional context parameters are needed in the future, this would require another breaking change.

### Temporarily Mutate Instance State

- **Description**: Temporarily mutate `self._logger` within a try/finally block
- **Pros**: Simple; no signature changes for internal layers or public protocol
- **Cons**: Not thread-safe; could cause subtle bugs in multi-threaded applications; difficult to reason about
- **Reason for Rejection**: Thread safety is a fundamental requirement. Secret management libraries are often used in concurrent environments (web servers, async code), so thread safety cannot be compromised.

## Future Direction

- If additional context information is needed in the future (e.g., request IDs, retry counts, timeout values), consider introducing a context object. This would be another breaking change to the `SecretProvider` protocol, but is acceptable in 0.x versions.
- The pattern established here (explicit parameter propagation) should be followed for any similar cross-cutting concerns
- Monitor for any performance issues related to parameter passing, though none are expected given the overhead is negligible
- Document the breaking change clearly in release notes, including migration examples for custom provider implementations

## References

- Issue #40: Add logging support to envresolve
- ADR-0024: Core Design Principle of 'Fine-Grained Control' - This decision aligns with explicit configuration over implicit behavior
