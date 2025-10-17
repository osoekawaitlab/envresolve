"""Nox configuration file for envresolve project."""

import nox

nox.options.default_venv_backend = "uv"

PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.14"]


@nox.session(python="3.12")
def tests_unit(session: nox.Session) -> None:
    """Run unit tests only (requires Azure SDK for mocking)."""
    session.install("-e", ".[azure]", "--group=dev")
    session.run("pytest", "tests/unit/", "-v")


@nox.session(python="3.12")
def tests_e2e(session: nox.Session) -> None:
    """Run E2E tests only (requires Azure SDK for mocking)."""
    session.install("-e", ".[azure]", "--group=dev")
    session.run("pytest", "tests/e2e/", "-v")


@nox.session(python="3.12")
def tests(session: nox.Session) -> None:
    """Run all tests with coverage reporting (requires Azure SDK)."""
    session.install("-e", ".[azure]", "--group=dev")
    session.run(
        "pytest",
        "--cov=src/envresolve",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-fail-under=80",
    )


@nox.session(python=PYTHON_VERSIONS)
def tests_all_versions(session: nox.Session) -> None:
    """Run all tests across all supported Python versions."""
    session.install("-e", ".[azure]", "--group=dev")
    session.run("pytest")


@nox.session(python="3.12")
def tests_without_azure(session: nox.Session) -> None:
    """Run tests that don't require Azure SDK (excludes azure-dependent files)."""
    # Install only dev dependencies, not [azure]
    session.install("-e", ".", "--group=dev")

    # Run tests excluding Azure-dependent files and marked tests
    session.run(
        "pytest",
        "-m",
        "not azure",
        "--ignore=tests/unit/providers/test_azure_kv_provider.py",
        "--ignore=tests/e2e/test_azure_kv_resolution.py",
        "--ignore=tests/live/test_azure_kv_live.py",
        "--ignore=src/envresolve/providers/azure_kv.py",
        "-v",
    )


@nox.session(python="3.12")
def tests_live(session: nox.Session) -> None:
    """Run live integration tests against real Azure resources.

    Prerequisites (one-time setup):
      1. Configure: cd infra/terraform && cp terraform.tfvars.example terraform.tfvars
      2. Edit terraform.tfvars with your Azure credentials
      3. Create resources: terraform init && terraform apply
      4. Azure authentication: az login

    Before each test run:
      - Set environment variables: source scripts/setup_live_tests.sh

    Required environment variables:
      - ENVRESOLVE_LIVE_KEY_VAULT_NAME
      - ENVRESOLVE_LIVE_SECRET_NAME
      - ENVRESOLVE_LIVE_SECRET_VALUE
      - ENVRESOLVE_LIVE_SECRET_VERSION (optional)

    Note: Azure resources can be kept and reused. Run 'terraform destroy' only
          when cleanup is needed.
    """
    session.install("-e", ".[azure]", "--group=dev")
    session.run("pytest", "-m", "live", "tests/live/", "-v")


@nox.session(python="3.12")
def mypy(session: nox.Session) -> None:
    """Run mypy type checking (requires Azure SDK for type stubs)."""
    session.install("-e", ".[azure]", "--group=dev")
    session.run("mypy", "src/", "tests/")


@nox.session(python="3.12")
def lint(session: nox.Session) -> None:
    """Run ruff linting."""
    session.install("-e", ".", "--group=dev")
    session.run("ruff", "check", ".")


@nox.session(python="3.12")
def format_code(session: nox.Session) -> None:
    """Run ruff formatting."""
    session.install("-e", ".", "--group=dev")
    session.run("ruff", "format", ".")


@nox.session(python="3.12")
def quality(session: nox.Session) -> None:
    """Run all code quality checks (mypy, ruff)."""
    session.install("-e", ".[azure]", "--group=dev")
    session.run("mypy", "src/", "tests/")
    session.run("ruff", "check", ".")


@nox.session(python="3.12")
def check_all(session: nox.Session) -> None:
    """Run all checks and tests."""
    session.install("-e", ".[azure]", "--group=dev")
    session.run("pytest")
    session.run("mypy", "src/", "tests/")
    session.run("ruff", "check", ".")


@nox.session(python="3.12")
def docs_build(session: nox.Session) -> None:
    """Build documentation."""
    session.install("-e", ".", "--group=docs", "--group=dev")
    session.run("mkdocs", "build", "--strict")
