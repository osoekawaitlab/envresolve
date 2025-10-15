# Architecture Decision Record (ADR)

## Title

Conditional Doctest Skip Based on Optional Dependencies

## Status

Accepted

## Date

2025-10-13

## Context

Doctests in `api.py` demonstrate Azure Key Vault usage, but fail when `azure-identity` and `azure-keyvault-secrets` are not installed. Using `# doctest: +SKIP` unconditionally skips these examples even when Azure SDK is available, preventing validation of documentation examples.

We need doctests to:

- Run and validate when Azure SDK is installed
- Skip gracefully when Azure SDK is absent
- Work consistently across local development and CI environments

## Decision

Implement pytest fixture-based conditional skipping in root `conftest.py`:

```python
def _azure_sdk_available() -> bool:
    try:
        return (
            importlib.util.find_spec("azure.identity") is not None
            and importlib.util.find_spec("azure.keyvault.secrets") is not None
        )
    except (ImportError, ModuleNotFoundError):
        return False

@pytest.fixture(autouse=True)
def _skip_azure_doctests(request: pytest.FixtureRequest) -> None:
    if not isinstance(request.node, pytest.DoctestItem):
        return

    if "api.py" in str(request.node.fspath):
        azure_tests = ["register_azure_kv_provider", "load_env"]
        is_azure = any(name in request.node.name for name in azure_tests)
        if is_azure and not _azure_sdk_available():
            pytest.skip("Azure SDK not available")
```

Place in root `conftest.py` to apply to both `tests/` and `src/` (per `testpaths = ["tests", "src"]`).

## Rationale

- **Environment-aware**: Automatically detects Azure SDK availability
- **Test coverage**: Doctests run when dependencies are present
- **No manual intervention**: Users don't need to modify code based on their environment
- **Pytest integration**: Uses standard pytest skip mechanism

Static `# doctest: +SKIP` was rejected because it prevents testing when dependencies are available.

## Implications

### Positive Implications

- Doctests validate documentation accuracy when possible
- Graceful degradation without Azure SDK
- CI can test both scenarios (with/without optional deps)
- Consistent with `@pytest.mark.azure` strategy (ADR-0012)

### Concerns

- **Fixture complexity**: More complex than simple `+SKIP`
- **Name coupling**: Relies on doctest function names. *Mitigation*: Documented in fixture
- **Maintenance**: Future optional providers need fixture updates. *Mitigation*: Centralized in conftest.py

## Alternatives

### 1. Unconditional `# doctest: +SKIP`

- Simpler
- Rejected: Never validates doctests, even when Azure SDK present

### 2. Custom doctest directive (e.g., `+SKIP_IF_NO_AZURE`)

- More explicit in docstrings
- Rejected: Requires complex pytest doctest plugin customization

### 3. Separate doctest files for optional features

- Clear separation
- Rejected: Duplicates API documentation, harder to maintain

## Future Direction

- Extend pattern for other optional dependencies (AWS, GCP providers)
- Consider pytest plugin for cleaner syntax
- Add logging to show which doctests are skipped and why

## References

- Implementation: `conftest.py:17-46`
- Related: ADR-0012 (pytest markers for test files)
- Pytest docs: https://docs.pytest.org/en/stable/how-to/skipping.html
