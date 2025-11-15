# ADR 0023: Use fnmatch (Glob Patterns) for Pattern Matching Implementation

## Status

Accepted

## Date

2025-11-15

## Context

ADR-0022 introduced `ignore_patterns` parameter for pattern-based variable exclusion. This ADR addresses the implementation choice: **which pattern syntax to use for matching**.

Users need to specify patterns like:

- `PS*` - all shell prompt variables
- `TEMP_*` - all temporary variables
- `DEBUG_*` - all debug flags

We must choose a pattern matching format that is:

- Simple and familiar to users
- Sufficient for common use cases
- Maintainable (preferably standard library)

## Decision

Use Python's `fnmatch` module for glob-style pattern matching.

**Supported wildcards:**

- `*` - matches any characters (e.g., `PS*` matches `PS1`, `PS2`, `PROMPT`)
- `?` - matches single character (e.g., `PS?` matches `PS1`, but not `PS10`)
- `[seq]` - matches any character in seq (e.g., `PS[12]` matches `PS1`, `PS2`)

**Implementation:**

```python
import fnmatch

def _should_ignore_key(self, key: str, ignore_patterns: list[str] | None) -> bool:
    if ignore_patterns and any(
        fnmatch.fnmatch(key, pattern) for pattern in ignore_patterns
    ):
        return True
    return False
```

## Rationale

**Why glob patterns:**

- **Familiarity**: Users know glob from `.gitignore`, shell wildcards, file patterns
- **Simplicity**: Simpler syntax than regex (no need to escape special chars for basic cases)
- **Coverage**: Covers 90% of use cases without complexity
- **Low learning curve**: Most developers already understand `*` and `?`

**Why `fnmatch` module:**

- **Standard library**: No external dependencies
- **Well-tested**: Part of Python stdlib since early versions
- **Unix shell compatibility**: Consistent with shell glob behavior
- **Well-documented**: Official Python documentation available

**Performance characteristics:**

- Fast enough for typical use cases (< 100 patterns, < 1000 variables)
- Linear scan of patterns is acceptable for this use case
- Exact match check (`ignore_keys`) happens first as fast path

## Implications

### Positive Implications

- Users can write intuitive patterns: `PS*`, `TEMP_*`, `DEBUG_*`
- No learning curve for developers familiar with shell globs
- Standard library means no dependency management
- Consistent behavior across platforms

### Concerns

- **Limited expressiveness**: Cannot express complex patterns like "starts with PS and ends with digit"
    - Mitigation: Sufficient for 90% of use cases; regex can be Phase 3 if needed
- **Performance with many patterns**: O(n*m) for n variables and m patterns
    - Mitigation: Typical use has < 10 patterns; acceptable performance

## Alternatives

### Regex Patterns

Use Python's `re` module for regex matching:

```python
import re

patterns = [r"^PS\d+$", r"^PROMPT.*", r"^TEMP_.*"]
if any(re.match(pattern, key) for pattern in patterns):
    return True
```

**Pros:**

- More powerful and expressive
- Can express complex patterns

**Cons:**

- **Higher learning curve**: Regex is complex for non-experts
- **Overkill**: Most use cases don't need regex power
- **Error-prone**: Easy to write incorrect regex patterns
- **Less readable**: `^PS.*$` vs. `PS*`

**Rejected:** Glob covers most use cases with simpler syntax. If complex patterns are needed, we can add regex support in Phase 3 without breaking glob patterns.

### Custom Pattern Language

Design a custom pattern syntax:

```python
patterns = ["starts_with:PS", "ends_with:_TMP", "contains:DEBUG"]
```

**Pros:**

- Tailored to exact needs
- Very explicit

**Cons:**

- **New syntax to learn**: No existing familiarity
- **Implementation complexity**: Need to write parser
- **Maintenance burden**: Custom code to maintain
- **Limited adoption**: No ecosystem support

**Rejected:** Reinventing the wheel when glob patterns work well.

### Simple String Methods

Use only string prefix/suffix matching:

```python
if any(key.startswith(prefix) for prefix in prefixes):
    return True
```

**Pros:**

- Very simple, no dependencies
- Fast

**Cons:**

- **Too limited**: Cannot express "ends with" and "contains" patterns in one syntax
- **Multiple parameters needed**: `ignore_prefixes`, `ignore_suffixes`, `ignore_contains`
- **Less flexible**: Cannot combine patterns like `PS[12]`

**Rejected:** Too limited compared to glob patterns. Glob provides better expressiveness without complexity.

## Future Direction

- **Phase 3 (if needed)**: Add regex pattern support via separate parameter (`ignore_regex`)
    - Can coexist with glob patterns
    - Users choose based on complexity needs
    - Example: `ignore_patterns=["PS*"], ignore_regex=[r"^VAR\d{3}$"]`

- **Performance optimization**: If profiling shows issues:
    - Compile patterns once and cache
    - Use trie-based matching for large pattern sets

## References

- ADR-0022: Add ignore_patterns Parameter for Pattern-Based Variable Exclusion
- Python fnmatch documentation: <https://docs.python.org/3/library/fnmatch.html>
- Unix glob patterns: <https://man7.org/linux/man-pages/man7/glob.7.html>
- Issue #25: Add ignore_patterns parameter with glob matching support
