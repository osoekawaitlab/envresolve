"""Custom exceptions for envresolve."""


class CircularReferenceError(Exception):
    """Raised when a circular reference is detected in variable expansion."""
