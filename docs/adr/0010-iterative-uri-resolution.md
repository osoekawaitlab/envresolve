# Architecture Decision Record (ADR)

## Title

Iterative URI Resolution with Cycle Detection

## Status

Accepted

## Date

2025-01-13

## Context

Secret URIs may resolve to values containing other URIs or variables requiring further expansion. This occurs in scenarios like:

- Gradual migration: `akv://vault/old-name` → `"akv://vault/new-name"` → actual secret
- Multi-level indirection for access control or configuration management
- Variable expansion in resolved values: `akv://vault/indirect` → `"akv://vault/${KEY}"` → needs expansion

Without iterative resolution, users would need manual multi-step resolution. We need to maintain idempotency (plain strings return unchanged) while detecting circular references.

## Decision

Implement iterative resolution in `SecretResolver.resolve()` with cycle detection using a `seen` set:

```python
seen = set()
current = uri

while True:
    if current in seen:
        raise CircularReferenceError(variable_name=current, chain=[*list(seen), current])
    seen.add(current)

    expanded = expand_variables(current, env)
    if not is_secret_uri(expanded):
        return expanded  # Termination: not a URI

    resolved = provider.resolve(parse_secret_uri(expanded))
    if resolved == current:
        return resolved  # Termination: stable value

    current = resolved
```

## Rationale

- **Idempotency**: Plain strings and non-target URIs return immediately without provider calls
- **Flexibility**: Supports arbitrary nesting depth and mixed variable/URI resolution
- **Safety**: `seen` set guarantees cycle detection without infinite loops
- **Simplicity**: Single resolution entry point handles all cases uniformly

## Implications

### Positive Implications

- Users can chain URIs across vaults for access control patterns
- Variable expansion works at any nesting level
- Backward compatibility: existing single-level URIs work unchanged
- Idempotency ensures safe repeated calls

### Concerns

- **Performance**: Multiple provider calls increase latency. *Mitigation*: Future TTL cache (ADR-pending)
- **Debugging**: Long resolution chains are hard to trace. *Mitigation*: `CircularReferenceError` includes full chain
- **Complexity**: Harder to reason about multi-step resolution. *Mitigation*: Comprehensive E2E tests (7 test cases)

## Alternatives

### 1. Single-pass resolution only

- Simpler implementation
- Rejected: Users would need manual multi-step calls

### 2. Recursive resolution

- More functional style
- Rejected: Stack overflow risk, harder to track seen values

### 3. Fixed depth limit (e.g., max 10 iterations)

- Simpler termination logic
- Rejected: Arbitrary limit; cycle detection is more robust

## Future Direction

- Add resolution metrics/logging for observability
- Consider optional depth limit as safety net (configurable, default disabled)
- Implement TTL cache to reduce redundant provider calls
- Evaluate async resolution for parallel multi-vault lookups

## References

- E2E tests: `tests/e2e/test_nested_resolution.py`
- Unit tests: `tests/unit/test_resolver.py`
- Implementation: `src/envresolve/application/resolver.py:34-95`
