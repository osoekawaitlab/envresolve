# Architecture Decision Record (ADR)

## Title

Use Custom Exception Hierarchy Instead of Built-in Exceptions

## Status

Accepted

## Date

2025-10-11

## Context

The envresolve library needs to handle various error conditions during variable expansion (e.g., missing variables, circular references). We must decide whether to:

1. Use Python's built-in exceptions (KeyError, ValueError, RuntimeError)
2. Create custom exception classes specific to envresolve

## Decision

Create a custom exception hierarchy with a base exception class (`EnvResolveError`) and specific exception types for each error condition (e.g., `VariableNotFoundError`, `CircularReferenceError`).

## Rationale

- **Selective error handling**: Clients can catch `EnvResolveError` to handle all library errors or catch specific exceptions for fine-grained control
- **Clear API contract**: Custom exceptions document what errors the library can raise
- **Namespace isolation**: Prevents accidental catching of unrelated KeyError/ValueError from other code
- **Domain semantics**: Exception names reflect domain concepts (`VariableNotFoundError` is clearer than `KeyError`)
- **Future extensibility**: Easy to add new exception types as features are added
- **Prevents leakage**: Internal implementation details (like using dict for env) don't leak into the API

## Implications

### Positive Implications

- Clients can write `except EnvResolveError` to catch all library errors
- Clear separation between library errors and other Python errors
- Better IDE support with domain-specific exception names
- Exception hierarchy can evolve independently from implementation
- Easier to add exception-specific attributes and methods

### Concerns

- Slightly more boilerplate code (exception class definitions)
- Developers must remember to use custom exceptions instead of built-ins

Mitigation: Exception classes are stable and infrequently modified. The benefits far outweigh the minimal overhead.

## Alternatives

### Use Built-in Exceptions

Raise `KeyError` for missing variables, `RuntimeError` for circular references.

```python
if var_name not in env:
    raise KeyError(var_name)
```

- **Pros**: No extra code, familiar to Python developers
- **Cons**:
  - Cannot distinguish library errors from other KeyError in client code
  - Poor semantic clarity (KeyError doesn't convey "variable not found in expansion")
  - Tight coupling to implementation (exposes that we use dict internally)
  - Cannot catch "all envresolve errors" without catching unrelated errors
- **Rejection reason**: Lack of namespace isolation and poor API clarity

### Exception Wrapper Pattern

Catch built-in exceptions and wrap them.

```python
try:
    value = env[var_name]
except KeyError as e:
    raise VariableNotFoundError(...) from e
```

- **Pros**: Clear API boundary, custom exceptions for clients
- **Cons**: Still need to define custom exceptions (same as our decision)
- **Note**: This pattern is actually used in our implementation for internal error handling, but the key decision is to *expose* custom exceptions in the public API

## Future Direction

- Consider adding exception base class methods for common operations (e.g., `to_dict()` for structured logging)
- Add exception hierarchy documentation to API reference
- Evaluate if recovery/retry strategies should be exception attributes

## References

- Python Exception Hierarchy: https://docs.python.org/3/library/exceptions.html#exception-hierarchy
- PEP 3151: Reworking the OS and IO exception hierarchy
- Issue #1: Variable expansion feature implementation
