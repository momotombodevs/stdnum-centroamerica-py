"""Package exceptions.

No message includes the number that was received: it may be personal data.
"""

from __future__ import annotations

__all__ = ["StdnumError", "UnknownDocumentError", "UnsupportedOperationError"]


class StdnumError(Exception):
    """Base class of every exception raised by the package."""


class UnknownDocumentError(StdnumError, LookupError):
    """The key matches neither a bundled nor a registered document."""


class UnsupportedOperationError(StdnumError, TypeError):
    """The document does not support the requested operation (``parse`` or ``generate``)."""
