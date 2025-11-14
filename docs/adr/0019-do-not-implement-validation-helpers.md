# ADR 0019: Do Not Implement Validation Helper Functions and Metadata Query Helpers

## Status

Accepted

## Date

2025-11-12

## Context

The v0.1.x roadmap included two features:

- Validation helpers for string-based API (`is_resolved`, `needs_expansion`, `is_secret_uri`)
- Optional metadata/query helpers for resolved values

These were proposed as convenience utilities to help users validate strings and query resolution metadata.

## Decision

Do not implement these features.

## Rationale

### Validation Helpers

1. **Trivial pattern matching**: Functions like `is_resolved()` reduce to simple checks (`'$' in string`) that users can write in one line.
2. **Unclear use cases**: No concrete scenarios identified where pre-validation provides value over direct resolution with error handling.
3. **API bloat**: Adding public functions increases maintenance burden, documentation overhead, and testing requirements without clear benefit.
4. **Premature abstraction**: Exposes internal parsing logic as public API, constraining future implementation changes.

### Metadata Query Helpers

1. **Undefined requirements**: The roadmap item lacks concrete specification of what metadata would be tracked or how it would be queried.
2. **No identified use cases**: Without specific user needs, this is speculative feature development (YAGNI principle).

## Implications

### Positive Implications

- Maintains focused, minimal API surface
- Reduces maintenance overhead
- Preserves implementation flexibility

### Concerns

- If users request these features, they will need custom implementations
- Mitigation: Revisit this decision if concrete use cases emerge from user feedback

## Alternatives

**Provide utility functions anyway**: Would offer convenience but at the cost of API complexity and maintenance burden without proven demand.

## Future Direction

Reopen this decision if:

- Multiple users independently request similar validation functionality
- Specific use cases emerge that cannot be solved with existing APIs
- Internal parser complexity makes user-side validation significantly error-prone
