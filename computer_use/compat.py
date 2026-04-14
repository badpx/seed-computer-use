"""Python compatibility checks."""

from __future__ import annotations

import sys

MIN_PYTHON = (3, 8)
def python_version_text(version_info: tuple[int, int] | None = None) -> str:
    """Return a human readable major.minor version string."""
    version = version_info or (sys.version_info.major, sys.version_info.minor)
    return f"{version[0]}.{version[1]}"


def is_supported_python(version_info: tuple[int, int] | None = None) -> bool:
    """Return whether the current Python version is supported."""
    version = version_info or (sys.version_info.major, sys.version_info.minor)
    return MIN_PYTHON <= version


def get_python_compatibility_error(version_info: tuple[int, int] | None = None) -> str | None:
    """Return a clear compatibility error for unsupported Python versions."""
    version = version_info or (sys.version_info.major, sys.version_info.minor)

    if version < MIN_PYTHON:
        return (
            f"当前 Python 版本为 {python_version_text(version)}，"
            f"至少需要 Python {python_version_text(MIN_PYTHON)}。"
        )

    return None


def ensure_supported_python() -> None:
    """Raise a RuntimeError if the current Python version is unsupported."""
    error = get_python_compatibility_error()
    if error:
        raise RuntimeError(error)
