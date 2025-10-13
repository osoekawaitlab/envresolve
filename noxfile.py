"""Nox configuration file for envresolve project."""

import nox

nox.options.default_venv_backend = "uv"

PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13"]


@nox.session(python="3.12")
def tests_unit(session: nox.Session) -> None:
    """Run unit tests only (requires Azure SDK for mocking)."""
    session.install("-e", ".[azure]", "--group=dev")
    session.run("uv", "run", "--active", "pytest", "tests/unit/", "-v")


@nox.session(python="3.12")
def tests_e2e(session: nox.Session) -> None:
    """Run E2E tests only (requires Azure SDK for mocking)."""
    session.install("-e", ".[azure]", "--group=dev")
    session.run("uv", "run", "--active", "pytest", "tests/e2e/", "-v")


@nox.session(python="3.12")
def tests(session: nox.Session) -> None:
    """Run all tests with coverage reporting (requires Azure SDK)."""
    session.install("-e", ".[azure]", "--group=dev")
    session.run(
        "uv",
        "run",
        "--active",
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
        "uv",
        "run",
        "--active",
        "pytest",
        "-m",
        "not azure",
        "--ignore=tests/unit/test_azure_kv_provider.py",
        "--ignore=tests/e2e/test_azure_kv_resolution.py",
        "--ignore=src/envresolve/providers/azure_kv.py",
        "-v",
    )


@nox.session(python="3.12")
def mypy(session: nox.Session) -> None:
    """Run mypy type checking (requires Azure SDK for type stubs)."""
    session.install("-e", ".[azure]", "--group=dev")
    session.run("uv", "run", "--active", "mypy", "src/", "tests/")


@nox.session(python="3.12")
def lint(session: nox.Session) -> None:
    """Run ruff linting."""
    session.install("-e", ".", "--group=dev")
    session.run("uv", "run", "--active", "ruff", "check", ".")


@nox.session(python="3.12")
def format_code(session: nox.Session) -> None:
    """Run ruff formatting."""
    session.install("-e", ".", "--group=dev")
    session.run("uv", "run", "--active", "ruff", "format", ".")


@nox.session(python="3.12")
def quality(session: nox.Session) -> None:
    """Run all code quality checks (mypy, ruff)."""
    session.install("-e", ".[azure]", "--group=dev")
    session.run("uv", "run", "--active", "mypy", "src/", "tests/")
    session.run("uv", "run", "--active", "ruff", "check", ".")


@nox.session(python="3.12")
def check_all(session: nox.Session) -> None:
    """Run all checks and tests."""
    session.install("-e", ".[azure]", "--group=dev")
    session.run("uv", "run", "--active", "pytest")
    session.run("uv", "run", "--active", "mypy", "src/", "tests/")
    session.run("uv", "run", "--active", "ruff", "check", ".")


@nox.session(python="3.12")
def docs_build(session: nox.Session) -> None:
    """Build documentation."""
    session.install("-e", ".", "--group=docs")
    session.run("uv", "run", "--active", "mkdocs", "build", "--strict")
