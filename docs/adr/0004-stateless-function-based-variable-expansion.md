# Architecture Decision Record (ADR)

## Title

Use Stateless Function for Variable Expansion Core Logic

## Status

Accepted

## Date

2025-10-11

## Context

The variable expansion service needs to provide a simple API for expanding `${VAR}` and `$VAR` references in strings. We must decide on the interface design:

1. **Stateless function**: `expand_variables(text, env)` - takes both text and environment dict as parameters
2. **Stateful class**: `VariableExpander(env)` with `expand(text)` method - environment configured at initialization
3. **Hybrid**: Stateless function as core, with convenience wrapper class for os.environ integration

Key considerations:

- Simplicity and ease of use
- Testability
- Flexibility for different use cases (.env files, os.environ, custom dicts)
- Performance (avoiding unnecessary object creation)

## Decision

Use a **stateless function** (`expand_variables(text, env)`) as the core API, with an `EnvExpander` convenience class for os.environ integration.

```python
# Core API: stateless function
def expand_variables(text: str, env: dict[str, str]) -> str:
    """Expand ${VAR} and $VAR in text using provided environment dictionary."""

# Convenience wrapper for os.environ
class EnvExpander:
    def expand(self, text: str) -> str:
        return expand_variables(text, dict(os.environ))
```

## Rationale

- **Simplicity**: Functions are simpler than classes for stateless operations
- **Explicit dependencies**: `env` parameter makes it clear what data is being used
- **Testability**: Easy to test with different env dicts without object creation
- **No unnecessary state**: No need to store `env` when it's only used during expansion
- **Performance**: Avoids object allocation for one-time expansions
- **Flexibility**: Callers can easily switch env dicts between calls
- **Pythonic**: Aligns with Python's preference for functions over classes when state is not needed
- **Convenience when needed**: `EnvExpander` provides a clean API for the common os.environ use case

## Implications

### Positive Implications

- Clear, simple API that's easy to understand and use
- No hidden state or side effects
- Easier to reason about in tests (no setup required)
- Can be used as a building block for higher-level abstractions
- Flexibility to use with any dict (os.environ, .env files, custom configs)
- Better performance for one-off expansions

### Concerns

- Slightly more verbose when repeatedly expanding with the same env dict
- Need to maintain consistency between function and class API

Mitigation: The `EnvExpander` class addresses the verbosity concern for the os.environ use case. For other repeated use cases, callers can use `functools.partial` if needed.

## Alternatives

### Stateful Class Only

Use a class with env configured at initialization:

```python
expander = VariableExpander(env)
result = expander.expand(text)
```

- **Pros**: Less repetition when using the same env multiple times
- **Cons**:
  - Unnecessary object creation for one-time use
  - Hidden state makes testing more complex
  - Need to create new objects to switch env dicts
  - Violates "functions over classes" principle when state is not needed
- **Rejection reason**: Adds complexity without sufficient benefit. State is not needed for this operation.

### Factory Functions

Provide factory functions for common cases:

```python
def create_expander(env: dict[str, str]) -> Callable[[str], str]:
    return lambda text: expand_variables(text, env)

def create_env_expander() -> Callable[[str], str]:
    return lambda text: expand_variables(text, dict(os.environ))
```

- **Pros**: Functional style, flexible
- **Cons**: Less discoverable than a class, lambda functions harder to debug
- **Rejection reason**: Class provides better IDE support and clearer intent than lambda

### Global State

Store environment in module-level variable:

```python
_env = {}

def set_environment(env: dict[str, str]) -> None:
    global _env
    _env = env

def expand(text: str) -> str:
    return expand_variables(text, _env)
```

- **Pros**: Very concise API
- **Cons**: Global mutable state, not thread-safe, makes testing difficult
- **Rejection reason**: Anti-pattern that causes numerous testing and concurrency issues

## Future Direction

- Consider adding `functools.lru_cache` decorator if profiling shows repeated parsing overhead
- If more configuration options are needed (e.g., custom patterns, escaping), consider a configuration object
- Monitor usage patterns; if most calls use os.environ, consider making it the default parameter

## References

- ADR 0001: Regular expressions for variable expansion
- Python Design Philosophy: "Simple is better than complex" (PEP 20)
- Issue #1: Variable expansion feature implementation
- Discussion: Function vs. Class API design
