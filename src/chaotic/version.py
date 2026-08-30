"""Single source of truth for the package version.

`pyproject.toml` reads `__version__` from this file at build time, so it must
stay a plain module level string literal without any imports.
"""

__version__ = "1.0.0"
