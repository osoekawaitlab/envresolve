# Architecture Decision Record (ADR)

## Title

Use Regular Expressions for Variable Expansion

## Status

Accepted

## Date

2025-10-10

## Context

The envresolve library needs to expand environment variable references in strings using `${VAR}` and `$VAR` syntax. The expansion must:

- Support both `${VAR}` and `$VAR` formats
- Handle multiple variables in a single string
- Enable future support for nested variable expansion
- Detect circular references
- Provide clear error messages when variables are missing

## Decision

Use Python's `re` module with regex pattern matching (`\$\{([^}]+)\}` for `${VAR}`) to implement variable expansion.

## Rationale

- **Simplicity**: Regex provides a concise way to match variable patterns
- **Standard library**: No additional dependencies required
- **Flexibility**: Easy to extend patterns for `$VAR` syntax and more complex cases
- **Performance**: Regex is efficient for this use case
- **Maintainability**: Pattern is clear and well-understood by Python developers

## Implications

### Positive Implications

- Minimal code required for basic expansion
- Easy to test with unit tests
- Fast execution for typical use cases
- Clear separation between pattern matching and value substitution

### Concerns

- Regex may become complex if we add many features (escaping, default values, etc.)
- Performance could degrade with very large strings or many variables
- Error messages from regex failures can be cryptic

Mitigation: Keep patterns simple and add custom validation/error handling as needed.

## Alternatives

### String Template (stdlib)

Python's `string.Template` class provides variable substitution.

- **Pros**: Built-in, simple API, safer than format strings
- **Cons**: Limited to `$VAR` and `${VAR}` only, less flexible for custom extensions
- **Rejection reason**: We need more control over expansion behavior (cycle detection, nested expansion)

### Manual String Parsing

Iterate through characters to find and replace variables.

- **Pros**: Complete control, potentially better error messages
- **Cons**: More complex to implement correctly, prone to edge case bugs, harder to maintain
- **Rejection reason**: Regex provides sufficient control with less complexity

### AST-based Parsing

Build an abstract syntax tree for variable references.

- **Pros**: Very flexible, excellent error handling
- **Cons**: Overkill for this use case, significant complexity overhead
- **Rejection reason**: Not justified for simple variable expansion

## Future Direction

- If complexity grows (escaping, default values, filters), consider migrating to a dedicated template engine
- Monitor performance with profiling; optimize regex patterns if needed
- Add support for `$VAR` syntax using additional regex pattern
- Implement nested expansion through recursive calls with cycle detection

## References

- Python `re` module documentation: https://docs.python.org/3/library/re.html
- Issue #1: Variable expansion in environment variables
