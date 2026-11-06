"""Pieces shared by the integrations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from stdnum_centroamerica._registry import canonical_form
from stdnum_centroamerica._types import Document, ErrorCode

Normalize = Literal["canonical", "compact", "format", "none"]
"""Form in which an integration returns a valid number.

``canonical`` is the form to store: the compact form, except where it would merge different
numbers (Panama keeps its hyphens). ``compact`` always strips separators."""

MESSAGES: Mapping[ErrorCode, str] = {
    ErrorCode.FORMAT: "Does not match the format of this document.",
    ErrorCode.COMPONENT: "Contains a date or code that does not exist.",
    ErrorCode.CHECKSUM: "The check digit does not match.",
}
"""Default messages."""


def missing_dependency(package: str, extra: str) -> ImportError:
    """Return an ``ImportError`` with the exact command to install the integration."""
    return ImportError(
        f"This integration requires {package}. Install it with: "
        f'pip install "stdnum-centroamerica[{extra}]" or uv add "stdnum-centroamerica[{extra}]"'
    )


def normalized(document: Document, value: str, normalize: Normalize) -> str:
    """Return the valid number in the requested form."""
    if normalize == "canonical":
        return canonical_form(document, value)
    if normalize == "compact":
        return document.compact(value)
    if normalize == "format":
        return document.format(value)
    return value


def check_normalize(normalize: str) -> None:
    if normalize not in ("canonical", "compact", "format", "none"):
        message = "normalize must be 'canonical', 'compact', 'format' or 'none'"
        raise ValueError(message)
