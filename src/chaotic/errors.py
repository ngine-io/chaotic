"""Exception hierarchy used across chaotic.

Every error raised on purpose derives from :class:`ChaoticError`, which lets the
CLI distinguish "we know what went wrong" from unexpected crashes.
"""

from __future__ import annotations


class ChaoticError(Exception):
    """Base class for every error raised deliberately by chaotic."""


class UnknownProviderError(ChaoticError):
    """The configured ``kind`` has no provider implementation."""
