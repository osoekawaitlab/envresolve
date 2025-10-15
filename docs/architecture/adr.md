# Architecture Decision Records (ADRs)

This page provides an overview of all architectural decisions made for envresolve.

## What are ADRs?

Architecture Decision Records document important architectural decisions along with their context and consequences. They help track the "why" behind design choices.

## Current ADRs

### ADR 0001: Variable Expansion with Regular Expressions

**Status**: Accepted
**Date**: 2025-10-11

Decided to use regular expressions for variable expansion instead of manual string parsing.

[View Full ADR](../adr/0001-variable-expansion-with-regex.md)

---

### ADR 0002: Custom Exception Hierarchy

**Status**: Accepted
**Date**: 2025-10-11

Established a custom exception hierarchy with base exceptions for better error handling.

[View Full ADR](../adr/0002-custom-exception-hierarchy.md)

---

### ADR 0003: Structured Exception Design

**Status**: Accepted
**Date**: 2025-10-11

Defined structured exception design for variable expansion errors.

[View Full ADR](../adr/0003-structured-exception-design.md)

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

[View Full ADR](../adr/0004-stateless-function-based-variable-expansion.md)

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

[View Full ADR](../adr/0005-string-based-api-with-idempotent-resolution.md)

---

### ADR 0006: Nested Variable Expansion Implementation

**Status**: Accepted
**Date**: 2025-10-13

Chose a two-phase iterative algorithm for supporting nested variable expansion like `${VAR_${NESTED}}`.

**Key Decision**: Expand innermost curly braces first, then simple variables, iterating until stable.

**Rationale**:

- Correct inside-out evaluation order
- Predictable behavior for complex nesting
- No recursion depth limits
- Clear error detection

[View Full ADR](../adr/0006-nested-variable-expansion-implementation.md)

---

### ADR 0007: Layer Separation (Services vs Application)

**Status**: Accepted
**Date**: 2025-10-13

Separated pure business logic (services layer) from environment integration (application layer).

**Key Decision**: Move `EnvExpander` and `DotEnvExpander` from `services/expansion.py` to `application/expanders.py`.

**Rationale**:

- Single Responsibility Principle
- Better testability (pure logic without I/O)
- Clear dependency direction
- Matches clean architecture patterns

[View Full ADR](../adr/0007-layer-separation-services-vs-application.md)

---

### ADR 0008: Circular Reference Chain Tracking

**Status**: Accepted
**Date**: 2025-10-13

Extended `CircularReferenceError` to include full reference chain for better debugging.

**Key Decision**: Add `chain: list[str]` attribute showing complete cycle (e.g., `["A", "B", "C", "A"]`).

**Rationale**:

- Immediate visibility of complete cycle
- Better debugging experience
- Programmatic access to cycle information
- Actionable error messages

[View Full ADR](../adr/0008-circular-reference-chain-tracking.md)

---

### ADR 0009: Manual Provider Registration Pattern

**Status**: Accepted
**Date**: 2025-10-13

Established manual provider registration with a global registry instead of auto-discovery or dependency injection.

**Key Decision**: Users explicitly call `register_azure_kv_provider()` before resolving secrets. Providers are stored in a module-level singleton registry.

**Rationale**:

- Opt-in dependencies (only load what you need)
- Explicit control over initialization timing
- Resource efficiency through singleton providers
- Clear API surface

[View Full ADR](../adr/0009-manual-provider-registration-pattern.md)

---

### ADR 0010: Iterative URI Resolution

**Status**: Accepted
**Date**: 2025-10-13

Implemented iterative resolution with cycle detection to support URI-to-URI resolution chains.

**Key Decision**: Use a `while` loop with a `seen` set to resolve URIs iteratively until a stable value is reached or a cycle is detected.

**Rationale**:

- Supports arbitrary nesting depth
- Maintains idempotency (plain strings pass through)
- Safe cycle detection without infinite loops
- Flexible for mixed variable/URI resolution

[View Full ADR](../adr/0010-iterative-uri-resolution.md)

---

### ADR 0011: Conditional Doctest Skip

**Status**: Accepted
**Date**: 2025-10-13

Implemented pytest fixture-based conditional skipping for doctests that require optional dependencies.

**Key Decision**: Use autouse fixture in `conftest.py` to detect Azure SDK availability and skip Azure-related doctests when dependencies are missing.

**Rationale**:

- Doctests validate documentation when dependencies are present
- Graceful degradation without Azure SDK
- Consistent with pytest marker strategy
- Avoids manual `+SKIP` directives

[View Full ADR](../adr/0011-conditional-doctest-skip.md)

---

### ADR 0012: Pytest Markers for Azure Dependencies

**Status**: Accepted
**Date**: 2025-10-13

Introduced dedicated pytest marker (`azure`) to isolate tests requiring optional Azure SDK dependencies.

**Key Decision**: Mark Azure-dependent tests with `@pytest.mark.azure` and provide `tests_without_azure` Nox session that excludes them.

**Rationale**:

- Core test suite runs without optional dependencies
- Clear signal for which tests require Azure
- CI can run lightweight and full test suites separately
- Minimal disruption for contributors

[View Full ADR](../adr/0012-pytest-markers-for-azure-dependencies.md)

---

### ADR 0013: Class-Based API Design

**Status**: Accepted
**Date**: 2025-10-14

Encapsulated resolution state in `EnvResolver` class with module-level facade for backward compatibility.

**Key Decision**: Introduce `EnvResolver` class that encapsulates provider registry and resolver instance, expose singleton instance through module-level functions.

**Rationale**:

- Eliminates `global` keyword usage
- Better testability (tests can instantiate isolated resolvers)
- Maintains simple module-level API
- Supports multiple resolver instances if needed

[View Full ADR](../adr/0013-class-based-api-design.md)

---

### ADR 0014: Importlib Lazy Import

**Status**: Accepted
**Date**: 2025-10-14

Used `importlib.import_module` for lazy loading of optional Azure SDK dependencies with rich error messages.

**Key Decision**: Defer Azure SDK imports until `register_azure_kv_provider()` is called, and raise `ProviderRegistrationError` (not `ImportError`) with helpful installation instructions when dependencies are missing.

**Rationale**:

- Users can import envresolve without Azure SDK
- Clear, actionable error messages
- Aligns with custom exception hierarchy (ADR-0002)
- Extensible pattern for future optional providers

[View Full ADR](../adr/0014-importlib-lazy-import.md)

---

### ADR 0015: Manage Azure Live Test Infrastructure with Terraform

**Status**: Accepted
**Date**: 2025-10-15

Standardized live Azure Key Vault testing with Terraform-managed resources and explicit pytest gating.

**Key Decision**: Use Terraform manifests in `infra/terraform` plus helper Nox sessions to provision/destroy a Key Vault and sample secret for live tests.

**Rationale**:

- Repeatable provisioning for contributors and CI
- Clear separation between mocked and live suites via markers
- Easier cleanup through scripted Terraform destroy

[View Full ADR](../adr/0015-terraform-managed-live-tests.md)

---

## ADR Template

All ADRs follow a consistent template defined in [ADR 0000: ADR Template](../adr/0000-adr-template.md).

## Contributing

When making significant architectural decisions, please:

1. Review existing ADRs to ensure consistency
2. Use the ADR template for new decisions
3. Document both what you chose AND what you rejected
4. Include the "why" behind your decision
