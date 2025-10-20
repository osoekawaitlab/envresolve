# Architecture Decision Record (ADR)

## Title

Align `load_env()` Parameter Signature with python-dotenv's `load_dotenv()`

## Status

Accepted

## Date

2025-10-20

## Context

The original `load_env()` function signature used `path: str | Path = ".env"` as its parameter:

```python
def load_env(path: str | Path = ".env", *, export: bool = True, override: bool = False):
    ...
```

This created migration friction for users switching from python-dotenv's `load_dotenv()`, which uses `dotenv_path: str | Path | None = None`:

```python
def load_dotenv(dotenv_path: str | Path | None = None, ...):
    ...
```

The differences:
1. **Parameter name**: `path` vs. `dotenv_path`
2. **Default value**: `.env` (explicit path) vs. `None` (search behavior)
3. **Search semantics**: When `None`, python-dotenv searches for `.env` starting from the current working directory

Users migrating from python-dotenv had to:
- Rename parameter: `load_dotenv()` → `load_env(path=...)`
- Change default behavior: `load_dotenv()` → `load_env(path=".env")`

## Decision

Change `load_env()` signature to match python-dotenv's `load_dotenv()`:

```python
def load_env(
    dotenv_path: str | Path | None = None,
    *,
    export: bool = True,
    override: bool = False,
) -> dict[str, str]:
    """Load environment variables from a .env file and resolve secret URIs.

    Args:
        dotenv_path: Path to .env file. If None, searches for .env in
            current directory. Mimics python-dotenv's load_dotenv() behavior.
            (default: None)
    ...
    """
    # When dotenv_path is None, use find_dotenv with usecwd=True
    if dotenv_path is None:
        dotenv_path = find_dotenv(usecwd=True)
    env_dict = {k: v for k, v in dotenv_values(dotenv_path).items() if v is not None}
    ...
```

### Implementation Details

When `dotenv_path=None`, we explicitly call `find_dotenv(usecwd=True)` before passing to `dotenv_values()`. This is necessary because:

1. `dotenv_values(None)` internally calls `find_dotenv()` (without `usecwd=True`)
2. `find_dotenv()` defaults to `usecwd=False`, which searches from `__file__` location
3. Since `api.py` is in `src/envresolve/`, the search would start there and walk up to project root
4. This could find the wrong `.env` file (e.g., project's dev `.env` instead of application's `.env`)

By using `find_dotenv(usecwd=True)`, we ensure the search starts from `os.getcwd()`, matching user expectations.

## Rationale

### For Users

- **Zero-friction migration**: Drop-in replacement for `load_dotenv()`
- **Intuitive behavior**: `None` means "search from current directory" (matches shell behavior)
- **Familiar API**: Same parameter name as python-dotenv

### For Maintainability

- **Explicit control**: We control search behavior instead of relying on `dotenv_values()` internals
- **Clear intent**: `find_dotenv(usecwd=True)` explicitly documents search semantics
- **Test reliability**: Tests that `os.chdir()` work correctly because search happens from cwd

## Implications

### Positive Implications

- Drop-in replacement for python-dotenv users
- More intuitive default behavior (search from cwd)
- Better aligned with shell conventions (`cd` changes where `.env` is found)

### API Changes

The `load_env()` signature was updated for better python-dotenv compatibility:

**Parameter Name**
```python
# Before
envresolve.load_env(path=".env")

# After
envresolve.load_env(dotenv_path=".env")
```

**Default Value**
```python
# Before: Explicit path, always loads `.env` in cwd
load_env()  # Loads ./.env

# After: None triggers search, finds .env from cwd
load_env()  # Searches for .env starting from cwd, walks up if not found
```

Most users have `.env` in the current directory, so behavior remains unchanged in practice.

### Search Behavior Differences from python-dotenv

**Important limitation**: `envresolve.load_env(None)` does not have identical search behavior to `python-dotenv`'s `load_dotenv(None)`:

- **python-dotenv**: `load_dotenv(None)` uses `find_dotenv(usecwd=False)`, which searches from the **calling script's file location**
- **envresolve**: `load_env(None)` uses `find_dotenv(usecwd=True)`, which searches from the **current working directory**

**Why the difference?**

When `usecwd=False`, `find_dotenv()` searches from the `__file__` location of the calling code. For python-dotenv (a library users import), this means the user's script location. For envresolve, it would mean the library's installed location (e.g., `site-packages/envresolve/api.py`), which is never the intended behavior.

Using `usecwd=True` provides the most intuitive behavior: search from where the user is running their script.

**For complete python-dotenv compatibility**, use this pattern:

```python
from dotenv import load_dotenv
import envresolve

# Use python-dotenv's search behavior
load_dotenv()  # Searches from calling script location, loads to os.environ

# Resolve secrets in os.environ
envresolve.register_azure_kv_provider()
envresolve.resolve_os_environ()  # Resolves akv:// URIs in os.environ
```

This approach:
- Preserves python-dotenv's exact search semantics
- Keeps envresolve focused on secret resolution
- Provides clear separation of concerns

## Alternatives

### Keep `path` parameter, only change default to `None`

**Pros**: Smaller breaking change (only default value)

**Cons**:
- Still migration friction (parameter name mismatch)
- Inconsistent with python-dotenv's established API
- Confusing documentation ("path" vs. "dotenv_path")

**Rejection reason**: Partial migration creates long-term API inconsistency.

### Add `dotenv_path` as alias, deprecate `path`

**Pros**: Gradual migration path

**Cons**:
- Increased complexity (two parameters doing the same thing)
- Deprecation warnings add friction
- Eventually needs breaking change anyway
- envresolve is v0.x, users expect breakage

**Rejection reason**: For v0.x libraries, clean break is better than deprecation cycle.

### Keep original signature, add `search=False` flag

**Pros**: No breaking change

**Cons**:
- Doesn't solve migration friction (parameter name still wrong)
- More complex API (two parameters to control one behavior)
- `path=".env", search=True` is confusing

**Rejection reason**: Adds complexity without solving the root problem.

## Future Direction

- Consider adding `load_env_strict(dotenv_path: str | Path)` that requires explicit path and never searches
- If users request it, add `usecwd` parameter to expose python-dotenv's search control: `load_env(dotenv_path=None, usecwd=True)`

## References

- Issue: #13 "Align load_env signature with load_dotenv"
- Implementation: `src/envresolve/api.py:129-183`
- Tests: `tests/e2e/test_load_env.py`
- python-dotenv docs: https://saurabh-kumar.com/python-dotenv/
- Related ADRs: 0013 (class-based API design)
