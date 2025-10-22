# ADR 0018: Granular Error Handling for Variable Expansion and Secret Resolution

## Status

Accepted

## Date

2025-10-21

## Context

When loading environment variables from `.env` files or `os.environ`, two distinct types of errors can occur:

1. **Variable expansion errors**: Variables referenced with `${VAR}` syntax cannot be resolved
2. **Secret resolution errors**: Secret URIs like `akv://vault/secret` fail to fetch from providers

The original implementation had a single `stop_on_error` flag that controlled both types of errors uniformly. However, real-world usage revealed different requirements for handling these error types.

### Key Insight: Different Error Types Need Different Handling

The original implementation had a single `stop_on_error` flag that controlled both types of errors uniformly. However, real-world usage revealed different requirements for handling these error types:

**Variable expansion errors** can have different severities:
- **Typos in `.env` files**: `DB_URL=${DATABSE_HOST}` (should be `DATABASE_HOST`) - should raise error
- **Optional variables**: `LOG_LEVEL=${LOG_LEVEL:-info}` where `LOG_LEVEL` might not exist - could be tolerable
- **System variables**: `$PS1` (bash/zsh) or `%PROMPT%` (Windows) contain literal `$` characters (e.g., `PS1="\u@\h:\w\$ "`) that trigger unintended expansion - could be tolerable

**Secret resolution errors** are consistently critical:
- If a secret URI (`akv://vault/secret`) fails to resolve, it indicates a real problem (network, permissions, missing secret)
- Silently ignoring resolution failures would leave `akv://vault/secret` as a literal string in `os.environ`
- This could cause hard-to-debug issues in application code

### Need for Granular Control

Users need different error handling strategies:
- **Default behavior (both `True`)**: Fail-fast for strict error detection
- **Selective suppression**: Users can set `stop_on_expansion_error=False` when they know certain variables might be missing (e.g., when processing `os.environ` that includes system variables)
- **Always report secret failures**: `stop_on_resolution_error=True` ensures intentional secret URIs are validated

A single `stop_on_error` flag cannot serve both needs. Future enhancements (ignore patterns) will provide more granular control for the expansion error case.

## Decision

Replace single `stop_on_error` parameter with two granular parameters in both `load_env()` and `resolve_os_environ()`:

```python
def load_env(
    dotenv_path: str | Path | None = None,
    *,
    export: bool = True,
    override: bool = False,
    stop_on_expansion_error: bool = True,
    stop_on_resolution_error: bool = True,
) -> dict[str, str]:
    ...

def resolve_os_environ(
    keys: list[str] | None = None,
    prefix: str | None = None,
    *,
    overwrite: bool = True,
    stop_on_expansion_error: bool = True,
    stop_on_resolution_error: bool = True,
) -> dict[str, str]:
    ...
```

**Error categorization:**

- `stop_on_expansion_error` controls: `VariableNotFoundError` only
- `stop_on_resolution_error` controls: `SecretResolutionError`
- `CircularReferenceError` is **always raised** (configuration error, cannot be suppressed)

## Rationale

### Why Two Categories Instead of Per-Error-Type Flags

We could have provided individual flags for each exception type (`stop_on_variable_not_found`, `stop_on_secret_resolution`, etc.), but this would:

- Complicate the API as new error types are added
- Make the mental model more complex for users
- Not align with how users think about the problem

Instead, grouping by **operation** (expansion vs resolution) provides:

- **Clear mental model**: Users understand "variable expansion" vs "secret fetching"
- **Stable API**: New error types fit into existing categories
- **User-centric**: Matches how users describe their needs ("I want to skip missing variables but not secret failures")

### Why CircularReferenceError is Always Raised

Unlike `VariableNotFoundError`, `CircularReferenceError` represents:

- **Infinite loop**: `A=${B}, B=${A}` can never resolve
- **Configuration mistake**: Never intentional
- **Safety issue**: Suppressing would hide a critical problem

Therefore, `CircularReferenceError` is excluded from `stop_on_expansion_error` control.

### Default Behavior

Both flags default to `True`, preserving fail-fast behavior for strict error detection. Users can selectively disable error handling by setting either flag to `False` when needed (e.g., `stop_on_expansion_error=False` to tolerate missing optional variables).

## Implications

### Positive Implications

1. **Strict by default**: Both flags default to `True`, providing fail-fast behavior that catches typos and configuration errors early
2. **Selective tolerance**: Users can set `stop_on_expansion_error=False` when processing `os.environ` with system variables like `$PS1` or `%PROMPT%` that contain `$` characters
3. **Flexible resilience**: Applications can choose to tolerate missing optional variables while still catching secret resolution failures
4. **Clear error reporting**: Immediate feedback on both configuration errors (by default) and secret provider issues
5. **Future-proof**: API won't need changes if new error types are added (they'll fit into expansion or resolution categories)
6. **Complements ignore patterns**: The default strict behavior works well with planned ignore pattern features (roadmap v0.1.x), where users can explicitly list variables to skip rather than silently ignoring all errors

### Concerns

1. **API surface increase**: Two new parameters per function
   - **Mitigation**: Parameters are optional with sensible defaults
2. **Potential confusion**: Users might not understand which errors belong to which category
   - **Mitigation**: Clear documentation with examples, explicit mention in docstrings
3. **Asymmetry**: CircularReferenceError is an expansion error but not controlled by the flag
   - **Mitigation**: Documented explicitly; safety justifies the exception

## Alternatives

### Alternative 1: Keep Single `stop_on_error` Flag

**Characteristics**: Original design with uniform error handling

**Pros**:
- Simpler API
- No decision needed about error categorization

**Cons**:
- Cannot handle shell prompt variables (must stop on all errors or none)
- All-or-nothing approach doesn't match user needs

**Rejected because**: Real-world usage (e.g., `$PS1` variables) requires different handling for expansion vs resolution errors.

### Alternative 2: Per-Exception-Type Flags

**Characteristics**: Individual flags like `stop_on_variable_not_found`, `stop_on_circular_reference`, `stop_on_secret_resolution`

**Pros**:
- Maximum flexibility
- Explicit control over each error type

**Cons**:
- API grows with each new error type
- Too granular for typical use cases
- Cognitive overhead: users must understand internal exception hierarchy

**Rejected because**: Over-engineered for current needs; expansion/resolution categorization is more intuitive.

### Alternative 3: Error Callback

**Characteristics**: Allow users to provide a callback function to decide whether to suppress each error

```python
def load_env(error_handler: Callable[[Exception, str], bool] = None):
    ...
```

**Pros**:
- Maximum flexibility
- Can implement complex error handling logic

**Cons**:
- Much more complex API
- Harder to use for simple cases
- Requires users to understand exception types

**Rejected because**: Too complex for the common use cases; boolean flags are more Pythonic.

### Alternative 4: Separate Functions

**Characteristics**: Provide separate `load_env_strict()` / `load_env_lenient()` variants

**Pros**:
- Clear intent from function name
- No parameter complexity

**Cons**:
- Doesn't solve granular control problem (still need to specify which errors to tolerate)
- API proliferation (need variants for each function)

**Rejected because**: Doesn't address the core need for separate expansion/resolution control.

## Future Direction

### Potential Future Enhancements

1. **Additional error categories**: If new operation types are added (e.g., validation, transformation), they would get their own `stop_on_*` parameters
2. **Error callbacks**: If users need more complex error handling logic, we could add optional callbacks while keeping the simple boolean flags for common cases
3. **Logging integration**: Consider adding optional logging of suppressed errors for debugging

### Triggers for Revisiting

- User feedback indicating the two-category model is insufficient
- New error types that don't fit cleanly into expansion or resolution categories
- Performance concerns with try/except overhead (unlikely but possible)

## References

- Issue #17: Granular Error Handling
- ADR-0002: Custom Exception Hierarchy
- Shell prompt variables (`$PS1`, `%PROMPT%`): Real-world use case that motivated this design
