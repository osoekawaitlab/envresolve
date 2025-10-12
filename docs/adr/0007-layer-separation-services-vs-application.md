# Architecture Decision Record (ADR)

## Title

Separate Services Layer (Pure Logic) from Application Layer (Environment Integration)

## Status

Accepted

## Date

2025-10-13

## Context

As envresolve evolved, the `services/expansion.py` module contained both:

- **Pure logic**: `expand_variables(text, env)` - stateless string transformation
- **Environment integration**: `EnvExpander`, `DotEnvExpander` - classes that access `os.environ` and read `.env` files

This mixing of concerns violated clean architecture principles:

- Services layer should contain pure business logic (testable without I/O)
- Environment/file I/O are infrastructure concerns
- Clear dependency direction ensures maintainability

The question: Where should `EnvExpander` and `DotEnvExpander` reside?

Options:

1. Keep everything in services layer (current state before this ADR)
2. Move expanders to a new application layer
3. Move expanders to an infrastructure layer
4. Create separate modules for each concern (services, io, etc.)

## Decision

Introduce an **application layer** and move `EnvExpander` and `DotEnvExpander` to `application/expanders.py`, while keeping `expand_variables` in `services/expansion.py`.

**Layer structure:**

```text
application/expanders.py    # EnvExpander, DotEnvExpander (environment integration)
    ↓ depends on
services/expansion.py       # expand_variables (pure logic)
    ↓ depends on
exceptions.py              # Domain exceptions
```

**Responsibility assignment:**

**Services layer** (`services/expansion.py`):

- Pure string transformation logic
- `expand_variables(text: str, env: dict[str, str]) -> str`
- No I/O, no external dependencies beyond stdlib
- Easily testable with any dictionary

**Application layer** (`application/expanders.py`):

- Integration with operating system and file system
- `EnvExpander` - reads from `os.environ`
- `DotEnvExpander` - reads from `.env` files
- Coordinates services layer with external systems

## Rationale

**Why separate layers?**

- **Single Responsibility Principle**: Each layer has one reason to change
  - Services: Change when expansion logic needs modification
  - Application: Change when integration with environment/files changes
- **Testability**: Pure logic can be tested without mocking `os.environ` or file system
- **Reusability**: `expand_variables` can be used in any context, not just with environment variables
- **Clear dependencies**: Application depends on services, never the reverse

**Why "application" layer over "infrastructure"?**

- **Common terminology**: Application layer coordinates business logic with external systems
- **Infrastructure typically means**: Lower-level concerns (database, network, logging)
- **Expanders are use-case coordinators**: They adapt the pure expansion service to specific environments
- **Follows CLAUDE.md**: Already defined layered architecture with application layer

**Why not keep in services?**

- Services should be pure and I/O-free
- Mixing pure logic with I/O makes testing harder
- Violates dependency inversion principle (high-level policy mixed with low-level details)

## Implications

### Positive Implications

- **Clear boundaries**: Easy to identify pure logic vs. integration code
- **Better testability**:
  - Services: Test with simple dictionaries
  - Application: Mock only the environment/file system, not expansion logic
- **Easier to extend**: New integrations (e.g., `ConfigFileExpander`) go in application layer
- **Dependency graph clarity**: Obvious which direction dependencies flow
- **Matches established patterns**: Follows Clean Architecture, Hexagonal Architecture principles

### Concerns

- **More files**: Instead of one `expansion.py`, now have `services/expansion.py` and `application/expanders.py`
  - Mitigation: Better organization outweighs small increase in file count
- **Import path changes**: Public API imports from two places
  - Mitigation: `__init__.py` exports both, so users only see `envresolve.expand_variables`, etc.
- **Over-engineering risk**: Small library might not need this complexity
  - Mitigation: Separation is simple and pays dividends as library grows

## Alternatives

### Keep Everything in Services Layer

Keep `expand_variables`, `EnvExpander`, `DotEnvExpander` together in `services/expansion.py`.

- **Pros**:
  - Fewer files
  - Everything related to expansion in one place
  - Simpler import structure
- **Cons**:
  - Mixed responsibilities (pure logic + I/O)
  - Harder to test pure logic without mocking
  - Dependency inversion violation
  - Services layer depends on `os`, `pathlib`, `dotenv`
- **Rejection reason**: Sacrifices architectural clarity for minor convenience

### Move to Infrastructure Layer

Create `infrastructure/environment.py` and `infrastructure/files.py` for expanders.

- **Pros**:
  - Clear I/O boundary
  - Infrastructure layer is common pattern
- **Cons**:
  - Infrastructure typically means low-level adapters (database, network)
  - Expanders are use-case coordinators, not low-level adapters
  - Creates confusion about infrastructure vs. application
- **Rejection reason**: Incorrect use of "infrastructure" terminology

### Flatten into Multiple Modules

Create separate modules at same level:

- `expansion.py` - pure logic
- `env_integration.py` - `EnvExpander`
- `file_integration.py` - `DotEnvExpander`

- **Pros**:
  - Very granular separation
  - Easy to find specific functionality
- **Cons**:
  - No clear layer structure
  - Harder to understand dependency direction
  - Too many small files for small library
- **Rejection reason**: Over-fragmentation without clear architectural benefit

### Inline into Public API

Move expanders to `api.py` alongside public API exports.

- **Pros**:
  - All public-facing code in one place
  - Minimal files
- **Cons**:
  - `api.py` becomes dumping ground for everything
  - No separation of concerns
  - Harder to extend with more expander types
- **Rejection reason**: API layer should be thin facade, not contain implementations

## Future Direction

- **Additional application-layer components**:
  - `application/resolver.py` - Secret URI resolution orchestration (when implementing `akv://` support)
  - `application/cache.py` - TTL caching for resolved secrets
  - `application/loaders.py` - High-level `load_env()` functionality

- **Potential infrastructure layer**: If we add adapters for external systems:
  - `infrastructure/azure_kv.py` - Azure Key Vault client adapter
  - `infrastructure/aws_secrets.py` - AWS Secrets Manager adapter
  - These would be low-level I/O adapters, distinct from application coordinators

- **Re-evaluate if library grows**: If services layer grows to 10+ modules, consider:
  - Domain-driven design with aggregates
  - More sophisticated layering (use cases, repositories, etc.)

- **Document in CLAUDE.md**: Update architecture section to reflect layer boundaries and responsibilities

## References

- Clean Architecture (Robert C. Martin): https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html
- Hexagonal Architecture (Alistair Cockburn): https://alistair.cockburn.us/hexagonal-architecture/
- CLAUDE.md: Project architecture section defining layer structure
- Implementation: `src/envresolve/application/expanders.py`, `src/envresolve/services/expansion.py`
- Issue discussion: API redesign and layer separation
