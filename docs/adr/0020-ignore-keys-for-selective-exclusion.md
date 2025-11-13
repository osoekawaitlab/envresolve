# ADR 0020: Add ignore_keys Parameter for Selective Variable Exclusion

## Status

Accepted

## Date

2025-11-13

## Context

System environment variables (`$PS1`, `$PS2`, `%PROMPT%`) contain literal `$` characters (e.g., `PS1="\u@\h:\w\$ "`). When processing these with `resolve_os_environ()`, the `$` triggers unintended variable expansion, causing `VariableNotFoundError`.

The existing `stop_on_expansion_error=False` suppresses all expansion errors, preventing detection of legitimate typos in configuration.

## Decision

Add `ignore_keys` parameter to `load_env()` and `resolve_os_environ()`:

```python
def load_env(..., ignore_keys: list[str] | None = None) -> dict[str, str]: ...
def resolve_os_environ(..., ignore_keys: list[str] | None = None) -> dict[str, str]: ...
```

Variables in `ignore_keys` skip expansion/resolution and are included as-is. Phase 1 uses exact string matching only.

## Rationale

**Phase 1: List-based exact matching**
- Solves the immediate problem (system variables)
- Simple mental model
- Foundation for future pattern matching

**Why not patterns from the start:**
- Increases scope and complexity
- List-based approach provides immediate value
- Patterns can be added incrementally without breaking changes

## Implications

### Positive Implications

- Selective exclusion with strict error checking for other variables
- Complements granular error handling (ADR-0018)
- Non-breaking addition (optional parameter)

### Concerns

- Manual specification required for each key
  - **Mitigation**: Phase 2 will add glob patterns

## Alternatives

### Glob Patterns Immediately

**Pros**: More flexible, fewer manual specifications

**Cons**: More complex, increases initial scope

**Rejected**: Incremental approach provides faster value

### Callback Function

**Pros**: Maximum flexibility

**Cons**: Overkill for typical use cases, harder to configure

**Rejected**: List-based approach covers 90% of use cases

### Automatic Detection

**Pros**: Zero configuration

**Cons**: Magic behavior, platform-specific, users lose control

**Rejected**: Explicit configuration is more predictable

## Future Direction

- **Phase 2**: `ignore_patterns` with glob matching (`PS*`, `PROMPT*`)
- **Phase 3**: `ENVRESOLVE_IGNORE` environment variable
- **Potential**: Case-insensitive matching, regex patterns, invert logic

## References

- Issue #20: Add ignore_keys parameter
- ADR-0018: Granular Error Handling
