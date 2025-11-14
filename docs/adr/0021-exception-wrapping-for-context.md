# ADR 0021: Exception Wrapping for Variable Resolution Context

## Status

Accepted

## Date

2025-11-14

## Context

When `load_env()` or `resolve_os_environ()` fails to resolve a variable, the error message doesn't indicate which environment variable was being processed. For example, with `VAR2=${UNDEFINED}`, the error says "Variable not found: UNDEFINED" but not that the problem occurred in `VAR2`.

This makes debugging difficult when `.env` files have many variables or multiple variables reference the same underlying variable.

## Decision

Wrap `VariableNotFoundError` and `SecretResolutionError` with `EnvironmentVariableResolutionError` that includes:

- `context_key`: The environment variable name being processed
- `original_error`: The underlying exception
- Error message combining both pieces of information

```python
except (VariableNotFoundError, SecretResolutionError) as e:
    msg = f"Failed to resolve environment variable '{key}': {e}"
    raise EnvironmentVariableResolutionError(msg, context_key=key, original_error=e) from e
```

Wrapping occurs in `load_env()` and `resolve_os_environ()` at the application layer. `CircularReferenceError` is NOT wrapped as it already indicates the problematic variable chain.

## Rationale

### Application Layer Wrapping

- Only `api.py` has the context (`key`); service layer doesn't know which variable it's processing
- Keeps service layer generic and reusable (ADR-0007)
- Exception chain (`from e`) preserves original error location

### New Exception Type

- Preserves existing exception contracts (service layer doesn't need application context)
- Provides both programmatic access (`context_key`, `original_error`) and human-readable messages
- Allows catching either the wrapper or original exception types

## Implications

### Positive Implications

- Error messages clearly indicate which variable failed
- Programmatic error handling via attributes
- Works seamlessly with `stop_on_expansion_error` and `stop_on_resolution_error` (ADR-0018)
- Clean layer separation

### Concerns

- Breaking change for exception catching
    - **Mitigation**: Most users don't catch these; can access `original_error` if needed
- Wrapping logic duplicated in two methods
    - **Mitigation**: Simple pattern; extraction would add complexity

## Alternatives

### Modify Existing Exceptions

**Pros**: No new exception type

**Cons**: Violates layer separation, makes service layer less reusable

**Rejected**: Service layer shouldn't depend on application context

### Add Context to Message Only

**Pros**: Simpler implementation

**Cons**: No programmatic access, still violates layer separation

**Rejected**: Doesn't enable programmatic error handling

## Future Direction

- Structured error reporting for all failed variables
- Batch error collection option
- Custom error formatters

## References

- Issue #22: Add context to resolution errors
- ADR-0007: Layer Separation
- ADR-0018: Granular Error Handling
