# Architecture Decision Record (ADR)

## Title

Use String-Based API with Idempotent Resolution Instead of Data Models

## Status

Accepted

## Date

2025-10-12

## Context

As a library for resolving environment variables and secret URIs, envresolve must decide how to represent resolved values in its public API. There are two main approaches:

1. **Model-based API**: Return structured data models (e.g., Pydantic models) with metadata
2. **String-based API**: Return plain strings with utility functions for validation

Key considerations:
- End users ultimately need string values to set as environment variables
- Library should integrate seamlessly with existing code
- Users should not be forced to perform type conversions
- Resolution should be safe to call multiple times (idempotent)

The library's positioning as an **infrastructure utility** (not a domain framework) heavily influences this decision.

## Decision

Use a **string-based API with idempotent resolution** and provide utility functions for validation.

**Core principles:**
1. All public resolution functions return `str`
2. Resolution is idempotent (safe to call multiple times on already-resolved values)
3. Provide validation utilities (`is_resolved()`, `needs_expansion()`, `is_secret_uri()`)
4. Use data models internally for type safety, but hide them from public API

**API design:**
```python
# Resolution returns str directly
secret = resolve("akv://vault/secret")  # → str
secret = resolve(secret)  # → str (idempotent, no error)

# Validation utilities
is_resolved("akv://vault/secret")  # → False
is_resolved("actual-secret-value")  # → True
needs_expansion("${VAULT}/secret")  # → True
is_secret_uri("akv://vault/secret")  # → True
```

## Rationale

**Why string-based API:**
- **Zero friction**: Users get exactly what they need (strings for `os.environ`)
- **No conversion overhead**: No need to extract `.value` or call conversion methods
- **Easy integration**: Works with existing code that expects strings
- **Library positioning**: Infrastructure utilities should be transparent, not opinionated

**Why idempotent resolution:**
- **Safety**: Can safely apply `resolve()` to already-resolved values
- **Composability**: Easy to chain or apply conditionally without checks
- **Simplicity**: User doesn't need to track resolution state manually

**Why validation utilities:**
- **Explicit control**: Users can check state before resolution if needed
- **Debugging**: Easy to verify if a value is resolved or needs processing
- **Flexibility**: Enables conditional logic based on value state

## Implications

### Positive Implications

- **Superior user experience**: Minimal API surface, intuitive usage
- **Easy adoption**: No learning curve for basic usage
- **Type safety internally**: Can still use Pydantic models for internal validation
- **Flexible integration**: Works with any code expecting strings
- **Performance**: No object allocation overhead in hot paths

### Concerns

- **Less metadata**: Cannot return source location, resolution timestamp, etc.
- **String validation**: Determining if a string is "resolved" requires heuristics

**Mitigation:**
- Metadata can be provided through separate functions if needed (e.g., `get_resolution_info()`)
- Validation functions use well-defined rules (e.g., "no URI schemes, no variable references")

## Alternatives

### Model-Based API with Metadata

Return structured results with metadata:

```python
result = resolve("akv://vault/secret")  # → ResolutionResult
secret = result.value  # → str
source = result.source  # → "akv://vault/secret"
```

**Pros:**
- Rich metadata (source, timestamp, cache status, etc.)
- Type-safe error handling
- Explicit success/failure state

**Cons:**
- **Friction**: Users must extract `.value` every time
- **Type conversion overhead**: Extra step for the common case
- **Complex API**: More to learn, more verbose code
- **Poor fit**: Environment variables are fundamentally strings

**Rejection reason**: The overhead of type conversion outweighs metadata benefits. Users prioritize simplicity for infrastructure code.

### Non-Idempotent Resolution with Strict Validation

Raise errors when resolving already-resolved values:

```python
resolve("akv://vault/secret")  # → str
resolve("actual-secret-value")  # → Error: not a URI
```

**Pros:**
- Explicit error on misuse
- Forces user awareness

**Cons:**
- **Not composable**: Cannot safely chain operations
- **User burden**: Must track resolution state manually
- **Fragile**: Breaks if applied twice by accident

**Rejection reason**: Idempotency is more valuable than strict validation in infrastructure code.

### Hybrid Approach with Optional Metadata

Provide both simple and rich APIs:

```python
# Simple (returns str)
secret = resolve("akv://...")

# Rich (returns model)
result = resolve_with_metadata("akv://...")
```

**Pros:**
- Best of both worlds
- User chooses complexity level

**Cons:**
- **API bloat**: Two APIs to maintain
- **Confusion**: Which one to use?
- **Maintenance burden**: Keep both in sync

**Rejection reason**: Adds complexity without clear benefit. Simple API with separate utility functions is cleaner.

## Future Direction

- Consider adding optional logging/tracing for debugging (e.g., via context manager)
- If metadata needs emerge, provide separate query functions: `get_source()`, `get_resolution_time()`
- Monitor usage patterns; if metadata is frequently needed, reconsider hybrid approach in v2.x

## References

- ADR 0004: Stateless Function-Based Variable Expansion (established pattern of simple APIs)
- Discussion: Data models vs. string-based API for environment variable library
- Python stdlib `os.environ` - exclusively string-based, established pattern
- Issue #1: Variable expansion feature (informed by user needs)
