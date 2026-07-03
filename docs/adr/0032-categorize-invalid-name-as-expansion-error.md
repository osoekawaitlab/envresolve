# ADR 0032: Categorize `InvalidVariableNameError` as a Suppressible Expansion Error

## Status

Accepted

## Date

2026-07-03

## Context

ADR-0018 introduced two granular flags, `stop_on_expansion_error` and `stop_on_resolution_error`, and grouped failures by the operation that produces them. Its categorization named `VariableNotFoundError` as the only failure controlled by `stop_on_expansion_error`, with `CircularReferenceError` always raised.

`InvalidVariableNameError` (ADR-0002 hierarchy) is raised during variable expansion when a `${...}` reference contains a name that is not a valid identifier. In practice this also fires for `${...}` syntax that envresolve does not support, such as bash's alternate-value expansion `${VAR:+word}`. The name part parsed out of such a reference is not a valid identifier, so expansion rejects it.

This failure mode is common with shell-provided environment variables that were never authored for envresolve. The default Debian/Ubuntu `PS1` contains `${debian_chroot:+($debian_chroot)}`. When such a variable is present in `os.environ`, resolving it raises `InvalidVariableNameError`.

Because `InvalidVariableNameError` belonged to neither category, it propagated unconditionally — even when `stop_on_expansion_error=False` was explicitly requested. This aborted the entire resolution loop over `os.environ`, defeating the exact use case that `stop_on_expansion_error=False` exists to serve: tolerating system variables that cannot be expanded.

## Decision

Categorize `InvalidVariableNameError` as an expansion failure controlled by `stop_on_expansion_error`, alongside `VariableNotFoundError`.

- When `stop_on_expansion_error=False`, a variable whose value triggers `InvalidVariableNameError` is skipped and the loop continues.
- When `stop_on_expansion_error=True` (the default), the error is wrapped with context, consistent with how `VariableNotFoundError` is reported.

`CircularReferenceError` remains always raised and is unaffected by this decision.

## Rationale

**Operation-based grouping (ADR-0018):** The error occurs during the expansion operation, so by ADR-0018's own principle of grouping failures by operation it belongs to the expansion category. ADR-0018 anticipated that new error types would fit into the existing categories; this applies that intent.

**Same real-world motivation as `VariableNotFoundError`:** Both are triggered by system/shell variables (such as `PS1`) that were never intended as envresolve input. The motivating use case for `stop_on_expansion_error=False` in ADR-0018 was exactly these system variables.

**Not a configuration error like `CircularReferenceError`:** A circular reference can never resolve and is always an authoring mistake, which justifies always raising it. An unsupported or malformed `${...}` reference inside a value the user does not control is safe to skip when leniency is explicitly requested.

**Strict by default is preserved:** The default remains `True`, so genuine typos in user-authored `.env` files (for example `${:-default}` or `${1VAR}`) still surface immediately. Only explicit opt-in leniency skips them.

## Implications

### Positive Implications

- The `resolve_os_environ` / `load_env` leniency contract now holds for real-world environments: exporting a variable such as `PS1` no longer aborts resolution when `stop_on_expansion_error=False`.
- Under the default strict behavior, `InvalidVariableNameError` is now wrapped in `EnvironmentVariableResolutionError` with the offending key as context, matching `VariableNotFoundError` instead of leaking a raw, context-free exception.
- ADR-0018's categorization is broadened: `stop_on_expansion_error` now controls `VariableNotFoundError` and `InvalidVariableNameError`.

### Concerns

**Malformed user input can be silently skipped:** With `stop_on_expansion_error=False`, a genuine typo that produces an invalid name is skipped rather than reported.

*Mitigation:* This matches the existing trade-off already accepted for `VariableNotFoundError`. The strict default catches these cases; leniency is an explicit opt-in.

## Alternatives

### Keep `InvalidVariableNameError` always raised (like `CircularReferenceError`)

- **Pros**: No categorization change; malformed references always surface.
- **Cons**: `stop_on_expansion_error=False` cannot tolerate common system variables (`PS1`), which contradicts the purpose of the flag; a single unsupported value aborts the whole loop.
- **Rejection reason**: Unlike a circular reference, this failure is neither unresolvable-by-definition nor necessarily user-authored, and always raising it breaks the documented leniency use case.

### Add a dedicated `stop_on_invalid_name_error` flag

- **Pros**: Maximum control over this specific failure.
- **Cons**: Grows the API with each new error type and reintroduces the per-exception-type flags that ADR-0018 already rejected.
- **Rejection reason**: ADR-0018 deliberately groups by operation for a stable, intuitive API.

## References

- ADR-0002: Custom Exception Hierarchy
- ADR-0018: Granular Error Handling for Variable Expansion and Secret Resolution
- ADR-0024: Core Design Principle of "Fine-Grained Control"
- ADR-0026: Strategy for Exception Handling and Error Reporting
- ADR-0031: Support Default Values in Variable Expansion (`${VAR:-default}` Syntax)
