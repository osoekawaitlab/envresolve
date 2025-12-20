# ADR 0031: Support Default Values in Variable Expansion (`${VAR:-default}` Syntax)

## Status

Accepted

## Date

2025-12-20

## Context

Users need fallback values when environment variables are undefined or empty. This is a common pattern in shell scripting where `${VAR:-default}` provides a default value if VAR is not set or is empty.

Without default value support, users must ensure all referenced variables are defined, which creates configuration burden and reduces flexibility. Applications often need sensible defaults for optional configuration (e.g., `${PORT:-8080}`, `${LOG_LEVEL:-info}`).

## Decision

Implement `${VAR:-default}` syntax in variable expansion where:

- Uses the variable's value if it is defined and non-empty
- Uses the default value if the variable is undefined or empty string
- Default values are expanded recursively (can contain other variables)
- Works with the existing two-phase expansion algorithm
- Maintains circular reference detection

## Rationale

**User expectation:** Bash `:-` syntax is widely understood by developers familiar with shell scripting. Following established conventions reduces learning curve.

**Practical utility:** Empty strings often indicate misconfiguration or missing environment variables. Treating empty as "not set" aligns with Bash behavior and provides better user experience.

**Minimal changes:** Implementation builds on existing two-phase algorithm (ADR-0006) without modifying core expansion logic. Keeps regex patterns simple (ADR-0001) by parsing captured groups rather than adding regex complexity.

**Recursive expansion:** Default values can contain variables (e.g., `${VAR:-${FALLBACK}}`), enabling powerful fallback chains.

**Security:** No logging of default values (ADR-0030). Default values are treated as regular expansion input.

## Implications

### Positive Implications

- Enables sensible defaults in configuration
- Reduces configuration burden (fewer required environment variables)
- Maintains backward compatibility (no syntax conflicts with existing patterns)
- Recursive defaults enable complex fallback strategies
- No performance impact (default parsing only when `:-` detected)

### Concerns

**Empty string behavior:** Empty string is treated the same as undefined. This matches Bash `:-` but differs from Bash `-` (which only checks if unset).

*Mitigation:* This is the expected behavior for `:-` syntax. If users need to distinguish empty from unset, that would require a different syntax (e.g., `${VAR-default}`), which can be added in a future enhancement.

**Multiple `:-` in default value:** Splitting on first `:-` allows colons in defaults (e.g., `${VAR:-http://example.com:8080}`), but `${VAR:-a:-b}` is interpreted as default=`a:-b`.

*Mitigation:* This is documented behavior and consistent with shell expansion. Users rarely need `:-` in default values.

**Performance with deeply nested defaults:** Recursive expansion of defaults could impact performance with deeply nested chains.

*Mitigation:* Existing recursive expansion already handles this. Performance characteristics unchanged (same code path).

**Self-referencing defaults behave differently from Bash:** In Bash, `${VAR:-$VAR}` returns empty string when VAR is undefined (the default `$VAR` evaluates to empty). In envresolve, this raises `CircularReferenceError` because the innermost-first processing detects `${VAR}` referencing itself.

*Mitigation:* This is a consequence of the two-phase expansion algorithm (ADR-0006) which processes innermost variables first. The circular reference detection correctly identifies this as a cycle. Users should not write self-referencing defaults; use a different variable name for fallbacks (e.g., `${VAR:-${VAR_FALLBACK}}`).

## Alternatives

### Only check undefined (not empty)

Treat empty string as a valid value, use default only if variable is not in environment.

- **Pros**: Distinguishes between "not set" and "intentionally empty"
- **Cons**: Contradicts Bash `:-` semantics; users expect empty to trigger default
- **Rejection reason**: User expectation for `:-` includes empty string check

### Use different syntax (`??`, `||`, etc.)

Use alternative syntax like `${VAR??default}` or `${VAR||default}`.

- **Pros**: No ambiguity with existing patterns
- **Cons**: Less familiar to users; diverges from established conventions
- **Rejection reason**: Bash `:-` is widely known and expected

### Add both `:-` and `-` syntax

Support both `${VAR:-default}` (check empty) and `${VAR-default}` (only check unset).

- **Pros**: Maximum flexibility; matches full Bash semantics
- **Cons**: Adds complexity for marginal benefit
- **Rejection reason**: Can be added later if users request it; start with most common case

## Future Direction

**Additional parameter expansion syntaxes** can be considered if needed:

- `:=` - Use and assign default value (modifies environment)
- `:?` - Error with message if undefined/empty
- `:+` - Use alternate value if defined
- `-` - Use default only if unset (not if empty)

**Trigger for reconsideration:** User requests for distinguishing empty from unset, or need for assignment behavior.

**Implementation note:** The parsing approach (`_parse_variable_spec()`) makes adding new syntaxes straightforward without modifying regex patterns.

## References

- Issue #43: Add default value syntax support
- ADR-0001: Use Regular Expressions for Variable Expansion (keep patterns simple)
- ADR-0006: Nested Variable Expansion Implementation (two-phase algorithm)
- ADR-0030: Logging Information Disclosure Boundaries (no logging of defaults)
- Bash Parameter Expansion: https://www.gnu.org/software/bash/manual/html_node/Shell-Parameter-Expansion.html
