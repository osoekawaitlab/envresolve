"""Nox configuration file for envresolve project."""

import nox

nox.options.default_venv_backend = "uv"

PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12", "3.13"]


@nox.session(python="3.12")
def tests_unit(session: nox.Session) -> None:
    """Run unit tests only."""
    session.install("-e", ".", "--group=dev")
    session.run("uv", "run", "--active", "pytest", "tests/unit/", "-v")


@nox.session(python="3.12")
def tests_e2e(session: nox.Session) -> None:
    """Run E2E tests only."""
    session.install("-e", ".", "--group=dev")
    session.run("uv", "run", "--active", "pytest", "tests/e2e/", "-v")


@nox.session(python="3.12")
def tests(session: nox.Session) -> None:
    """Run all tests with coverage reporting."""
    session.install("-e", ".", "--group=dev")
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
    session.install("-e", ".", "--group=dev")
    session.run("uv", "run", "--active", "pytest")


@nox.session(python="3.12")
def mypy(session: nox.Session) -> None:
    """Run mypy type checking."""
    session.install("-e", ".", "--group=dev")
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
    session.install("-e", ".", "--group=dev")
    session.run("uv", "run", "--active", "mypy", "src/", "tests/")
    session.run("uv", "run", "--active", "ruff", "check", ".")


@nox.session(python="3.12")
def check_all(session: nox.Session) -> None:
    """Run all checks and tests."""
    session.install("-e", ".", "--group=dev")
    session.run("uv", "run", "--active", "pytest")
    session.run("uv", "run", "--active", "mypy", "src/", "tests/")
    session.run("uv", "run", "--active", "ruff", "check", ".")
