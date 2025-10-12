# Architecture Decision Records (ADRs)

This page provides an overview of all architectural decisions made for envresolve.

## What are ADRs?

Architecture Decision Records document important architectural decisions along with their context and consequences. They help track the "why" behind design choices.

## Current ADRs

### ADR 0001: Variable Expansion with Regular Expressions
**Status**: Accepted
**Date**: 2025-10-11

Decided to use regular expressions for variable expansion instead of manual string parsing.

[View Full ADR](https://github.com/osoekawaitlab/envresolve/blob/main/docs/adr/0001-variable-expansion-with-regex.md)

---

### ADR 0002: Custom Exception Hierarchy
**Status**: Accepted
**Date**: 2025-10-11

Established a custom exception hierarchy with base exceptions for better error handling.

[View Full ADR](https://github.com/osoekawaitlab/envresolve/blob/main/docs/adr/0002-custom-exception-hierarchy.md)

---

### ADR 0003: Structured Exception Design
**Status**: Accepted
**Date**: 2025-10-11

Defined structured exception design for variable expansion errors.

[View Full ADR](https://github.com/osoekawaitlab/envresolve/blob/main/docs/adr/0003-structured-exception-design.md)

---

### ADR 0004: Stateless Function-Based Variable Expansion
**Status**: Accepted
**Date**: 2025-10-11

Chose a stateless function (`expand_variables()`) as the core API with convenience wrapper classes.

**Key Decision**: Use `expand_variables(text, env)` instead of a stateful `VariableExpander(env)` class.

**Rationale**:
- Simpler and more explicit
- No hidden state
- Better for testing
- More Pythonic for stateless operations

[View Full ADR](https://github.com/osoekawaitlab/envresolve/blob/main/docs/adr/0004-stateless-function-based-variable-expansion.md)

---

### ADR 0005: String-Based API with Idempotent Resolution
**Status**: Accepted
**Date**: 2025-10-12

Decided to use a string-based API instead of data models for resolution results.

**Key Decision**: Return `str` directly instead of `ResolutionResult` models.

**Rationale**:
- Users ultimately need strings for `os.environ`
- Zero conversion overhead
- Infrastructure utilities should be transparent
- Idempotent resolution is safer and more composable

[View Full ADR](https://github.com/osoekawaitlab/envresolve/blob/main/docs/adr/0005-string-based-api-with-idempotent-resolution.md)

---

## ADR Template

All ADRs follow a consistent template defined in [ADR 0000: ADR Template](https://github.com/osoekawaitlab/envresolve/blob/main/docs/adr/0000-adr-template.md).

## Contributing

When making significant architectural decisions, please:

1. Review existing ADRs to ensure consistency
2. Use the ADR template for new decisions
3. Document both what you chose AND what you rejected
4. Include the "why" behind your decision
