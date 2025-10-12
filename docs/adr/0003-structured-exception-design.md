# Architecture Decision Record (ADR)

## Title

Use Structured Exceptions with Data Attributes

## Status

Accepted

## Date

2025-10-11

## Context

Following ADR 0002 (Custom Exception Hierarchy), we have decided to use custom exceptions. This ADR addresses how to design those exception classes.

When designing custom exceptions, we can choose between:

1. **Message-based**: Pass error messages directly to exception constructors
2. **Structured**: Pass structured data (variable names, values) and construct messages within the exception class

## Decision

Use structured exceptions that accept specific data attributes (e.g., `variable_name`) and construct error messages internally within the exception class.

## Rationale

- **Consistency**: Error message format is standardized across the codebase
- **Programmatic access**: Callers can access structured data (e.g., `e.variable_name`) for logging, debugging, or recovery
- **Testability**: Tests can validate specific error conditions by checking attributes rather than fragile string matching
- **Internationalization**: Message templates can be changed without modifying call sites
- **Type safety**: IDE and type checkers can validate that correct parameters are passed

## Implications

### Positive Implications

- Clear separation between error data and error presentation
- Easier to extend exceptions with additional context (e.g., resolution suggestions)
- Better error handling in client code (can extract variable names programmatically)
- Consistent error message format across the library

### Concerns

- Slightly more code in exception class definitions
- Need to maintain message templates when adding new exception types

Mitigation: Exception classes are relatively stable; the benefits outweigh the minimal maintenance cost.

## Alternatives

### Message-based Exceptions

Pass complete error messages to exception constructors.

```python
raise VariableNotFoundError(f"Variable not found: {var_name}")
```

- **Pros**: Simple, minimal code, flexible message format
- **Cons**: Inconsistent messages, no programmatic access to error details, harder to test
- **Rejection reason**: Sacrifices structure and testability for minimal code savings

### Exception with Optional Message Override

Accept structured data but allow message override.

```python
class VariableNotFoundError(EnvResolveError):
    def __init__(self, variable_name: str, message: str | None = None):
        self.variable_name = variable_name
        msg = message or f"Variable not found: {variable_name}"
        super().__init__(msg)
```

- **Pros**: Flexibility for special cases
- **Cons**: Inconsistency risk if developers override messages arbitrarily
- **Rejection reason**: Flexibility not needed for this use case; consistency is more valuable

## Future Direction

- Consider adding helper methods for common error message patterns (e.g., `with_suggestion()`)
- If internationalization is needed, replace f-strings with message templates and localization framework
- Add structured logging integration that automatically logs exception attributes

## References

- ADR 0002: Custom Exception Hierarchy
- Python Exception Best Practices: https://docs.python.org/3/tutorial/errors.html
- Issue #1: Variable expansion feature implementation
