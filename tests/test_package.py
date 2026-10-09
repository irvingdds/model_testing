"""Smoke tests for the package."""

from laya_classification import __version__


def test_version_is_defined() -> None:
    """The package exposes a version."""
    assert __version__ == "0.1.0"
