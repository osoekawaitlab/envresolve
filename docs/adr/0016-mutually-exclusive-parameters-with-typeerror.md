# Architecture Decision Record (ADR)

## Title

Use TypeError-based Custom Exception for Mutually Exclusive Parameters

## Status

Accepted

## Date

2025-10-18

## Context

The `resolve_os_environ()` API accepts two filtering parameters: `keys` (list of specific keys) and `prefix` (filter by prefix and strip). These parameters serve different use cases and are mutually exclusive by design—specifying both creates ambiguous behavior.

We need to decide:

1. How to handle the case when both parameters are specified
2. What exception type to use
3. Whether to use built-in exceptions or custom domain exceptions

The options are:

1. **Silent precedence**: Let one parameter silently override the other
2. **Raise TypeError**: Use Python's built-in TypeError
3. **Raise ValueError**: Use Python's built-in ValueError
4. **Raise custom exception**: Create a domain-specific exception that also inherits from TypeError

## Decision

Create a custom exception `MutuallyExclusiveArgumentsError` that inherits from both `EnvResolveError` (domain base) and `TypeError` (standard library semantic), and raise it when both `keys` and `prefix` are specified.

```python
class MutuallyExclusiveArgumentsError(EnvResolveError, TypeError):
    """Raised when mutually exclusive arguments are specified together."""

    def __init__(self, arg1: str, arg2: str) -> None:
        self.arg1 = arg1
        self.arg2 = arg2
        msg = (
            f"Arguments '{arg1}' and '{arg2}' are mutually exclusive. "
            f"Specify either '{arg1}' or '{arg2}', but not both."
        )
        super().__init__(msg)
```

## Rationale

### Following Industry Standards

Research into established Python libraries revealed that `TypeError` is the standard exception for mutually exclusive parameters:

- **pandas**: Uses `TypeError` with message "Keyword arguments `items`, `like`, or `regex` are mutually exclusive" in `DataFrame.filter()`
- **pandas Exception Guidelines**: Explicitly states TypeError should be raised for "wrong number of arguments, mutually exclusive arguments"
- **Python argparse**: Provides `add_mutually_exclusive_group()` which raises TypeError on conflict

### Aligning with Existing ADRs

- **ADR-0002 (Custom Exception Hierarchy)**: Requires all library errors to inherit from `EnvResolveError` for selective error handling
- **ADR-0003 (Structured Exception Design)**: Requires exceptions to accept structured data (argument names) with internal message construction

### Benefits of Multiple Inheritance

Using `class MutuallyExclusiveArgumentsError(EnvResolveError, TypeError)`:

1. **Standard semantics**: `isinstance(e, TypeError)` returns True, aligning with Python conventions
2. **Domain isolation**: `isinstance(e, EnvResolveError)` returns True, allowing catch-all error handling
3. **Programmatic access**: `e.arg1` and `e.arg2` attributes enable structured error handling
4. **Clear user feedback**: Explicit error message prevents debugging confusion

### Better Than Silent Precedence

Rejecting silent precedence (keys takes priority over prefix):

- Users may not notice the bug until production
- Implicit priority rules must be documented and remembered
- No feedback when API is misused
- Harder to debug when unexpected behavior occurs

## Implications

### Positive Implications

- **Fail-fast**: Errors are caught at function call time, not through unexpected behavior
- **Clear API contract**: Users immediately understand the constraint
- **Consistent with ecosystem**: Follows patterns from pandas and argparse
- **Type-safe error handling**: Callers can catch either `TypeError`, `EnvResolveError`, or the specific exception
- **Structured data**: `arg1` and `arg2` attributes allow programmatic error handling

### Concerns

- **Slight verbosity**: Requires 2-3 lines of validation code at function entry
- **Breaking change**: Existing code passing both parameters will now raise an exception

*Mitigation*:

- The validation is minimal and centralized in one place
- No existing code should rely on this undefined behavior (it was just implemented)
- The error message clearly explains how to fix the issue

## Alternatives

### Alternative 1: Keys Takes Precedence (Silent)

```python
if keys is not None:
    keys_to_process = keys  # prefix ignored
elif prefix is not None:
    keys_to_process = [k for k in os.environ if k.startswith(prefix)]
```

**Pros**: Simple implementation, no exception handling needed
**Cons**:

- Implicit behavior must be documented
- Users may not notice their mistake
- Debugging confusion when prefix is silently ignored
- Not consistent with pandas patterns

**Rejection reason**: Poor user experience and against industry best practices

### Alternative 2: Built-in TypeError Only

```python
if keys is not None and prefix is not None:
    raise TypeError("Arguments 'keys' and 'prefix' are mutually exclusive")
```

**Pros**: Uses standard library exception
**Cons**:

- Cannot catch all envresolve errors with `except EnvResolveError`
- No structured access to which arguments conflicted
- Violates ADR-0002 (custom exception hierarchy)

**Rejection reason**: Breaks the domain exception hierarchy requirement

### Alternative 3: Built-in ValueError

```python
if keys is not None and prefix is not None:
    raise ValueError("Cannot specify both 'keys' and 'prefix'")
```

**Pros**: Also a built-in exception
**Cons**:

- `ValueError` semantics are for "right type, wrong value"
- This is a "wrong combination of arguments" case (TypeError semantics)
- pandas uses TypeError for this pattern, not ValueError

**Rejection reason**: Wrong exception semantics for this error type

### Alternative 4: Apply Both Parameters

```python
if keys is not None and prefix is not None:
    # Apply both: filter keys by prefix and strip
    keys_to_process = [k for k in keys if k.startswith(prefix)]
    strip_prefix = True
```

**Pros**: Maximally flexible
**Cons**:

- Overlapping concerns—prefix filtering can be done by the caller
- Adds complexity to the API surface
- Unclear semantics (does stripping still happen?)

**Rejection reason**: Unnecessary complexity; orthogonal concerns should be separated

## Future Direction

- Consider adding similar validation for other potential parameter conflicts in future APIs
- If multiple functions need mutual exclusivity checks, extract a reusable validator helper
- Monitor user feedback to see if other parameter combinations need similar treatment

## References

- pandas Exception Guidelines: <https://github.com/pandas-dev/pandas/wiki/Choosing-Exceptions-to-Raise>
- pandas DataFrame.filter() implementation pattern
- ADR-0002: Custom Exception Hierarchy
- ADR-0003: Structured Exception Design
- Issue #7: Add resolve_os_environ() API
- Implementation: `src/envresolve/exceptions.py`, `src/envresolve/api.py`
