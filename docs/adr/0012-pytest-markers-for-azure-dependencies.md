# Architecture Decision Record (ADR)

## Title

Use Pytest Marker to Isolate Azure-Dependent Tests

## Status

Accepted

## Date

2025-01-13

## Context

Optional Azure integrations (`azure-identity`, `azure-keyvault-secrets`) are not installed in every development or CI environment. When those packages are missing, importing Azure-specific test modules or running doctests that touch `envresolve.providers.azure_kv` causes hard failures, even though the core library and the majority of tests do not require Azure.

We need an approach that allows the core suite to run without the Azure SDK while retaining full coverage when the optional dependencies are present.

## Decision

Introduce a dedicated pytest marker (`azure`) and a complementary Nox session that excludes Azure-only modules when that marker is filtered out.

```python
# In Azure-focused test modules
import pytest

pytestmark = pytest.mark.azure


@pytest.mark.azure
def test_azure_feature() -> None:
    ...
```

```python
# noxfile.py
@nox.session(python="3.12")
def tests_without_azure(session: nox.Session) -> None:
    session.install("-e", ".", "--group=dev")  # without extras
    session.run(
        "pytest",
        "-m",
        "not azure",
        "--ignore=tests/unit/test_azure_kv_provider.py",
        "--ignore=tests/e2e/test_azure_kv_resolution.py",
        "--ignore=src/envresolve/providers/azure_kv.py",
    )
```

The explicit `--ignore` directives avoid import-time failures for modules that unconditionally import the Azure SDK.

## Rationale

- **Fail fast with clear signal**: Tests that require Azure are labelled explicitly; skipped when marker excluded, and failures clearly indicate missing registration.
- **Minimal disruption**: Core contributors can run `nox -s tests_without_azure` without installing Azure packages, while CI can still run the full suite via `nox -s tests`.
- **Consistency with doctests**: Aligns with ADR-0011, which conditionally skips Azure doctests; both mechanisms rely on the same marker vocabulary.
- **Discoverability**: The `azure` marker is declared in `pyproject.toml` under `pytest.ini_options.markers`, making usage visible to contributors.

## Implications

### Positive Implications

- Core regression suite (65 tests) executes without optional dependencies.
- CI pipelines can stage jobs: lightweight core run vs. full Azure-enabled run.
- Contributors immediately see which tests rely on Azure-specific behavior via the marker.

### Concerns

- **Command verbosity**: The combination of `-m "not azure"` with multiple `--ignore` flags is easy to mistype. *Mitigation*: Provide the `tests_without_azure` Nox session and document it in the contributor guide.
- **Synchronization**: When new Azure modules or tests are added, the ignore list must be updated. *Mitigation*: Future: Add to code review checklist to mark Azure tests and update Nox session.
- **Marker proliferation**: Future cloud providers may introduce additional markers. *Mitigation*: Document marker naming conventions and reuse the same pattern for other optional stacks if/when they arrive.

## Alternatives

### Always Install Azure Extras in CI

- **Pros**: Simplifies test invocation; no markers or ignores necessary.
- **Cons**: Forces every developer/CI job to install heavy dependencies and Azure native libraries. Does not solve local setups without the SDK.
- **Rejection reason**: Conflicts with the goal of running quickly on minimal environments.

### Skip Tests via `ImportError` Guards inside Modules

- **Pros**: Keeps pytest invocation simple.
- **Cons**: Module-level code still executes before the guard runs, leading to `ImportError`. Requires defensive code at the top of every module.
- **Rejection reason**: Duplicate boilerplate with fragile control flow; marker approach centralizes the policy.

### Separate Test Suite Command (Custom Script)

- **Pros**: Hide complexity behind a bespoke runner.
- **Cons**: Adds tooling to maintain; contributors still need to learn marker semantics eventually.
- **Rejection reason**: Nox already provides a lightweight orchestration layer; no need for another script.

## Future Direction

- Consider refactoring Azure modules to import dependencies lazily (see ADR-0014). Once implemented, we can drop some `--ignore` flags and rely solely on markers.
- Add similar markers for other optional providers (AWS, GCP) if/when they are introduced.
- Automate marker enforcement (e.g., pytest plugin that fails if Azure SDK is missing while unmarked Azure tests are collected).

## References

- Implementation: `noxfile.py::tests_without_azure`
- Marker declaration: `pyproject.toml [tool.pytest.ini_options].markers`
- Related ADRs: 0011 (conditional doctest skip), 0014 (lazy imports for optional providers)
- Test modules: `tests/unit/test_azure_kv_provider.py`, `tests/e2e/test_azure_kv_resolution.py`
