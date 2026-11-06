"""Validate, format and compact Central American identity and tax numbers.

Basic usage::

    >>> import stdnum_centroamerica as sca
    >>> sca.is_valid("sv.dui", "12345678-4")
    True
    >>> sca.validate("sv.dui", "12345678-5").error
    <ErrorCode.CHECKSUM: 'checksum'>
    >>> sca.make("ni.cedula").format("0010101900001n")
    '001-010190-0001N'

Each document has a ``country.document`` key; :func:`keys` lists them. The package has no
dependencies, performs no I/O and never stores or logs the numbers.
"""

from stdnum_centroamerica._base import MAX_INPUT_LENGTH, BaseDocument
from stdnum_centroamerica._registry import (
    describe,
    generate,
    is_valid,
    keys,
    make,
    parse,
    register,
    validate,
)
from stdnum_centroamerica._types import (
    Document,
    DocumentInfo,
    ErrorCode,
    Level,
    SupportsGenerate,
    SupportsParse,
    ValidationResult,
)
from stdnum_centroamerica.exceptions import (
    StdnumError,
    UnknownDocumentError,
    UnsupportedOperationError,
)

__version__ = "0.1.0"

__all__ = [
    "MAX_INPUT_LENGTH",
    "BaseDocument",
    "Document",
    "DocumentInfo",
    "ErrorCode",
    "Level",
    "StdnumError",
    "SupportsGenerate",
    "SupportsParse",
    "UnknownDocumentError",
    "UnsupportedOperationError",
    "ValidationResult",
    "__version__",
    "describe",
    "generate",
    "is_valid",
    "keys",
    "make",
    "parse",
    "register",
    "validate",
]
