# ADR 0022: Add ignore_patterns Parameter for Pattern-Based Variable Exclusion

## Status

Accepted

## Date

2025-11-15

## Context

ADR-0020 introduced `ignore_keys` parameter for exact string matching to exclude specific environment variables from expansion. However, users must list each variable individually:

```python
load_env(ignore_keys=["PS1", "PS2", "PS3", "PS4"])  # Verbose for related vars
```

For excluding multiple related variables (e.g., all shell prompt variables `PS*`, all Windows prompt variables `PROMPT*`), exact matching becomes verbose and error-prone. Users need pattern-based exclusion.

This is **Phase 2** of the ignore functionality roadmap outlined in ADR-0020.

## Decision

Add `ignore_patterns` parameter to `load_env()` and `resolve_os_environ()` for pattern-based variable exclusion:

```python
def load_env(..., ignore_patterns: list[str] | None = None) -> dict[str, str]: ...
def resolve_os_environ(..., ignore_patterns: list[str] | None = None) -> dict[str, str]: ...
```

**Pattern format is defined in ADR-0023 (implementation choice).**

**Execution order:**

1. Check `ignore_keys` (exact match)
2. If not matched, check `ignore_patterns` (pattern match)
3. If neither matched, perform resolution

## Rationale

**Why separate parameter from `ignore_keys`:**

- Clear intent: exact match vs. pattern match
- Avoids ambiguity (a literal key name vs. a pattern)
- Both can be used together for flexibility

**Why pattern-based approach:**

- Concise for excluding related variables
- Reduces manual listing and error-proneness
- Covers real-world use cases (system variables, temporary variables, debug flags)

## Implications

### Positive Implications

- Concise exclusion of related variables instead of listing each one
- Flexibility: combine exact and pattern matching
- Non-breaking: optional parameter, backward compatible
- Covers real-world use cases: `TEMP_*`, `DEBUG_*`, `PROMPT*`

### Concerns

- **Pattern complexity**: Users might write overly broad patterns
    - Mitigation: Documentation with best practices and examples
- **Pattern format choice**: Need to decide on pattern syntax
    - Addressed in ADR-0023 (implementation decision)

## Alternatives

### Callback Function

Allow custom filter function:

```python
def should_ignore(key: str) -> bool:
    return key.startswith("PS") or key.startswith("PROMPT")

load_env(ignore_filter=should_ignore)
```

**Pros:** Maximum flexibility

**Cons:**

- Complex for simple cases
- Cannot be serialized to config files
- Overhead for typical scenarios

**Rejected:** Pattern-based approach is simpler and covers most needs. Callback can be Phase 4 if needed.

### Extend ignore_keys to Accept Patterns

Modify `ignore_keys` to auto-detect and handle patterns:

```python
load_env(ignore_keys=["EXACT_VAR", "PS*"])  # Mixed
```

**Pros:** Single parameter

**Cons:**

- Ambiguous: Is `PS*` literal or pattern?
- Cannot exclude a variable literally named `PS*`
- Less explicit

**Rejected:** Separate parameters provide clearer intent.

## Future Direction

- **Phase 3**: `ENVRESOLVE_IGNORE` environment variable for global configuration
- **Pattern format evolution**: If users need more complex matching, consider additional pattern types (see ADR-0023)

## References

- ADR-0020: Add ignore_keys Parameter for Selective Variable Exclusion (Phase 1)
- ADR-0023: Use fnmatch (Glob Patterns) for Pattern Matching Implementation
- Issue #25: Add ignore_patterns parameter with glob matching support
