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

Chose a stateless function (`expand_variables()`) as the core API instead of a stateful class.

[View Full ADR](../adr/0004-stateless-function-based-variable-expansion.md)

---

### ADR 0005: String-Based API with Idempotent Resolution

**Status**: Accepted
**Date**: 2025-10-12

Return `str` directly instead of data models, with idempotent resolution (safe to call multiple times).

[View Full ADR](../adr/0005-string-based-api-with-idempotent-resolution.md)

---

### ADR 0006: Nested Variable Expansion Implementation

**Status**: Accepted
**Date**: 2025-10-13

Two-phase iterative algorithm: expand innermost `${...}` first, then simple `$VAR`.

[View Full ADR](../adr/0006-nested-variable-expansion-implementation.md)

---

### ADR 0007: Layer Separation (Services vs Application)

**Status**: Accepted
**Date**: 2025-10-13

Separated pure business logic (services layer) from environment integration (application layer).

[View Full ADR](../adr/0007-layer-separation-services-vs-application.md)

---

### ADR 0008: Circular Reference Chain Tracking

**Status**: Accepted
**Date**: 2025-10-13

Extended `CircularReferenceError` to include full reference chain (`chain: list[str]`) for better debugging.

[View Full ADR](../adr/0008-circular-reference-chain-tracking.md)

---

### ADR 0009: Manual Provider Registration Pattern

**Status**: Accepted
**Date**: 2025-10-13

Users explicitly call `register_azure_kv_provider()` before resolving secrets.

[View Full ADR](../adr/0009-manual-provider-registration-pattern.md)

---

### ADR 0010: Iterative URI Resolution

**Status**: Accepted
**Date**: 2025-10-13

Implemented iterative resolution with cycle detection to support URI-to-URI resolution chains.

[View Full ADR](../adr/0010-iterative-uri-resolution.md)

---

### ADR 0011: Conditional Doctest Skip

**Status**: Accepted
**Date**: 2025-10-13

Pytest fixture-based conditional skipping for doctests requiring optional dependencies.

[View Full ADR](../adr/0011-conditional-doctest-skip.md)

---

### ADR 0012: Pytest Markers for Azure Dependencies

**Status**: Accepted
**Date**: 2025-10-13

Introduced `@pytest.mark.azure` to isolate tests requiring optional Azure SDK dependencies.

[View Full ADR](../adr/0012-pytest-markers-for-azure-dependencies.md)

---

### ADR 0013: Class-Based API Design

**Status**: Accepted
**Date**: 2025-10-14

Encapsulated resolution state in `EnvResolver` class with module-level facade for backward compatibility.

[View Full ADR](../adr/0013-class-based-api-design.md)

---

### ADR 0014: Importlib Lazy Import

**Status**: Accepted
**Date**: 2025-10-14

Used `importlib.import_module` for lazy loading of optional Azure SDK dependencies with rich error messages.

[View Full ADR](../adr/0014-importlib-lazy-import.md)

---

### ADR 0015: Manage Azure Live Test Infrastructure with Terraform

**Status**: Accepted
**Date**: 2025-10-15

Standardized live Azure Key Vault testing with Terraform-managed resources.

[View Full ADR](../adr/0015-terraform-managed-live-tests.md)

---

### ADR 0016: TypeError-based Custom Exception for Mutually Exclusive Parameters

**Status**: Accepted
**Date**: 2025-10-18

Created `MutuallyExclusiveArgumentsError` inheriting from both `EnvResolveError` and `TypeError`.

[View Full ADR](../adr/0016-mutually-exclusive-parameters-with-typeerror.md)

---

### ADR 0017: Align load_env() Parameter with python-dotenv

**Status**: Accepted
**Date**: 2025-10-20

Changed `load_env()` signature to match python-dotenv's `load_dotenv()` for zero-friction migration.

[View Full ADR](../adr/0017-load-env-dotenv-path-parameter.md)

---

### ADR 0018: Granular Error Handling for Variable Expansion and Secret Resolution

**Status**: Accepted
**Date**: 2025-10-21

Split single `stop_on_error` flag into `stop_on_expansion_error` and `stop_on_resolution_error`.

[View Full ADR](../adr/0018-granular-error-handling.md)

---

### ADR 0019: Do Not Implement Validation Helper Functions and Metadata Query Helpers

**Status**: Accepted
**Date**: 2025-11-12

Decided not to implement validation helpers and metadata query helpers due to lack of concrete use cases.

[View Full ADR](../adr/0019-do-not-implement-validation-helpers.md)

---

### ADR 0020: Add ignore_keys Parameter for Selective Variable Exclusion

**Status**: Accepted
**Date**: 2025-11-13

Added `ignore_keys` parameter to selectively skip variable expansion for specified keys.

[View Full ADR](../adr/0020-ignore-keys-for-selective-exclusion.md)

---

### ADR 0021: Exception Wrapping for Variable Resolution Context

**Status**: Accepted
**Date**: 2025-11-14

Wrap resolution errors with `EnvironmentVariableResolutionError` to provide context about which environment variable failed.

[View Full ADR](../adr/0021-exception-wrapping-for-context.md)

---

### ADR 0022: Add ignore_patterns Parameter for Pattern-Based Variable Exclusion

**Status**: Accepted
**Date**: 2025-11-15

Added `ignore_patterns` parameter to selectively skip variable expansion using pattern matching.

[View Full ADR](../adr/0022-ignore-patterns-parameter.md)

---

### ADR 0023: Use fnmatch (Glob Patterns) for Pattern Matching Implementation

**Status**: Accepted
**Date**: 2025-11-15

Use Python's `fnmatch` module for glob-style pattern matching in `ignore_patterns`.

[View Full ADR](../adr/0023-use-fnmatch-for-pattern-matching.md)

---

### ADR 0024: Core Design Principle of 'Fine-Grained Control'

**Status**: Accepted
**Date**: 2025-11-17

Adopt "Fine-Grained Control" as a core design principle, prioritizing explicit configuration over implicit behavior.

[View Full ADR](../adr/0024-core-design-principle-of-fine-grained-control.md)

---

### ADR 0025: Strategy for Optional Dependencies and Extensibility

**Status**: Accepted
**Date**: 2025-11-17

Define a formal strategy for optional dependencies using `extras` and lazy-loading to keep the core library lightweight.

[View Full ADR](../adr/0025-strategy-for-optional-dependencies.md)

---

### ADR 0026: Strategy for Exception Handling and Error Reporting

**Status**: Accepted
**Date**: 2025-11-17

Formalize the strategy for exception handling, including a custom hierarchy, granular types, and contextual wrapping.

[View Full ADR](../adr/0026-strategy-for-exception-handling.md)

---

### ADR 0027: API Design for State Management (Class-Based Core with Default Instance Facade)

**Status**: Accepted
**Date**: 2025-11-17

Adopt a hybrid API design with a stateful core class (`EnvResolver`) and default instance facade functions.

[View Full ADR](../adr/0027-api-design-for-state-management.md)

---

### ADR 0028: Forbid All Implicit Configuration via Environment Variables

**Status**: Accepted
**Date**: 2025-11-17

Decided to forbid any feature that implicitly alters library behavior based on environment variables, to uphold the principles of security and explicit configuration.

[View Full ADR](../adr/0028-forbid-implicit-env-var-config.md)

---

### ADR 0029: Logger Propagation Through Layers

**Status**: Accepted
**Date**: 2025-11-25

Pass logger instances explicitly as parameters through all layers rather than mutating instance state, ensuring thread-safe logger override behavior.

[View Full ADR](../adr/0029-logger-propagation-through-layers.md)

---

### ADR 0030: Logging Information Disclosure Boundaries

**Status**: Accepted
**Date**: 2025-11-26

Default logging exposes only operation types and error categories, without specific values. Exceptions contain full details for application-level logging decisions.

[View Full ADR](../adr/0030-logging-information-disclosure-boundaries.md)

---

## ADR Template

All ADRs follow a consistent template defined in [ADR 0000: ADR Template](../adr/0000-adr-template.md).

## Contributing

When making significant architectural decisions, please:

1. Review existing ADRs to ensure consistency
2. Use the ADR template for new decisions
3. Document both what you chose AND what you rejected
4. Include the "why" behind your decision
