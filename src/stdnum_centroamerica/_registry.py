"""Document catalog and high-level functions (``is_valid``, ``validate``, ...)."""

from __future__ import annotations

import difflib
import functools
import re
import threading
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from stdnum_centroamerica import cr, gt, hn, mrz, ni, pa, sv
from stdnum_centroamerica._types import (
    Document,
    DocumentInfo,
    Level,
    SupportsGenerate,
    SupportsParse,
    ValidationResult,
)
from stdnum_centroamerica.exceptions import UnknownDocumentError, UnsupportedOperationError

__all__ = [
    "canonical",
    "canonical_form",
    "describe",
    "generate",
    "is_valid",
    "keys",
    "make",
    "parse",
    "register",
    "validate",
]

_C, _F = Level.COMPLETE, Level.FORMAT

_CATALOG: Mapping[str, DocumentInfo] = MappingProxyType(
    {
        info.key: info
        for info in (
            DocumentInfo("gt.nit", gt.Nit, "GT", "NIT", _C),
            DocumentInfo("gt.dpi", gt.Dpi, "GT", "DPI (CUI)", _C),
            DocumentInfo("sv.dui", sv.Dui, "SV", "DUI", _C),
            DocumentInfo("sv.nit", sv.Nit, "SV", "NIT", _C),
            DocumentInfo("sv.nrc", sv.Nrc, "SV", "NRC", _F),
            DocumentInfo("hn.identidad", hn.Identidad, "HN", "Número de identidad", _F),
            DocumentInfo("hn.rtn", hn.Rtn, "HN", "RTN", _F),
            DocumentInfo("ni.cedula", ni.Cedula, "NI", "Cédula", _F),  # the letter is opt-in
            DocumentInfo("ni.ruc", ni.Ruc, "NI", "RUC", _F),
            DocumentInfo("cr.cedula_fisica", cr.CedulaFisica, "CR", "Cédula física", _F),
            DocumentInfo("cr.cedula_juridica", cr.CedulaJuridica, "CR", "Cédula jurídica", _F),
            DocumentInfo("cr.dimex", cr.Dimex, "CR", "DIMEX", _F),
            DocumentInfo("cr.nite", cr.Nite, "CR", "NITE", _F),
            DocumentInfo("pa.cedula", pa.Cedula, "PA", "Cédula", _F),
            DocumentInfo("pa.ruc", pa.Ruc, "PA", "RUC", _F),
            DocumentInfo("mrz.td3", mrz.Td3, "ICAO", "Passport MRZ (TD3)", _C),
            DocumentInfo("mrz.td1", mrz.Td1, "ICAO", "ID card MRZ (TD1)", _C),
            DocumentInfo("mrz.td2", mrz.Td2, "ICAO", "ID document MRZ (TD2)", _C),
        )
    }
)

_KEY = re.compile(r"[a-z0-9]+\.[a-z0-9_]+", re.ASCII)
_ECHOABLE_KEY = re.compile(r"[a-z]+\.[a-z][a-z0-9_]*", re.ASCII)
"""Keys safe to repeat in an error: ``12345678.9`` matches ``_KEY`` but may be a number."""
_MAX_KEY_LENGTH = 64
_custom: dict[str, type[Document]] = {}
_lock = threading.Lock()


def _resolve(key: str) -> type[Document]:
    value: object = key  # runtime check: callers may not be type-checked
    if not isinstance(value, str):
        message = f"key must be a str, got {type(value).__name__}"
        raise TypeError(message)
    normalized = value.lower()
    cls = _custom.get(normalized)
    if cls is not None:
        return cls
    info = _CATALOG.get(normalized)
    if info is not None:
        return info.document_class

    if len(normalized) > _MAX_KEY_LENGTH or _ECHOABLE_KEY.fullmatch(normalized) is None:
        # Not shaped like a key: it may be a document number passed by mistake (arguments
        # swapped), which is personal data, so it is not echoed.
        message = "Unsupported document key (not shown: it does not look like 'country.document')"
        raise UnknownDocumentError(message)

    message = f"Unsupported document: {normalized!r}"
    suggestions = difflib.get_close_matches(normalized, keys(), n=3)
    if suggestions:
        message += f". Did you mean {', '.join(map(repr, suggestions))}?"
    raise UnknownDocumentError(message)


@functools.lru_cache(maxsize=256)
def _cached(cls: type[Document], options: tuple[tuple[str, Any], ...]) -> Document:
    return cls(**dict(options))


def make(key: str, /, **options: Any) -> Document:
    """Return an instance of document ``key`` (e.g. ``"ni.cedula"``) built with ``options``.

    Keys are case-insensitive. Instances are immutable and reused.

    :raises UnknownDocumentError: if the key does not exist.
    :raises TypeError: if the document does not accept an option.
    """
    cls = _resolve(key)
    items = tuple(sorted(options.items()))
    try:
        return _cached(cls, items)
    except TypeError:
        # Options that cannot be used as a cache key (or invalid ones: the constructor
        # raises the same TypeError again).
        return cls(**options)


def validate(key: str, number: str, /, **options: Any) -> ValidationResult:
    """Validate ``number`` and return the failure reason (``result.error``), if any."""
    return make(key, **options).validate(number)


def is_valid(key: str, number: str, /, **options: Any) -> bool:
    """Return ``True`` if ``number`` is a valid ``key`` document."""
    return make(key, **options).is_valid(number)


def generate(key: str, /, **options: Any) -> str:
    """Return a synthetic valid number, for tests and sample data.

    It is random and may match a real number by chance: never use it as personal data.

    :raises UnsupportedOperationError: if the document does not generate numbers.
    """
    document = make(key, **options)
    if not isinstance(document, SupportsGenerate):
        message = f"Document {key.lower()!r} does not generate numbers"
        raise UnsupportedOperationError(message)
    return document.generate()


def parse(key: str, number: str, /, **options: Any) -> Any:
    """Return the components of a valid number, or ``None`` if it is invalid.

    Available for ``ni.cedula``, ``hn.identidad``, ``gt.dpi``, ``pa.cedula`` and the MRZs.
    The components are personal data and are not checked against any registry.

    :raises UnsupportedOperationError: if the document has no components to parse.
    """
    document = make(key, **options)
    if not isinstance(document, SupportsParse):
        message = f"Document {key.lower()!r} has no components to parse"
        raise UnsupportedOperationError(message)
    return document.parse(number)


def canonical_form(document: Document, number: str) -> str:
    """Return ``document.canonical(number)``, or the compact form if the class lacks it.

    Registered classes only have to implement :class:`Document`, which has no ``canonical``.
    """
    method = getattr(document, "canonical", None)
    if callable(method):
        return str(method(number))
    return document.compact(number)


def canonical(key: str, number: str, /, **options: Any) -> str:
    """Return the form to store: two different numbers never share it, and variants of the same
    number (separators, case, leading zeros where they carry no meaning) do.

    It is the compact form, except in Panama, where the hyphens are part of the number. Like
    :meth:`Document.compact`, it does not validate: call it on valid numbers.
    """
    return canonical_form(make(key, **options), number)


def keys() -> tuple[str, ...]:
    """Return the available keys: first those added with :func:`register`, then bundled ones."""
    with _lock:
        custom = tuple(_custom)
    return custom + tuple(key for key in _CATALOG if key not in _custom)


def describe() -> tuple[DocumentInfo, ...]:
    """Return the bundled documents with country, name and level. Registered ones are omitted."""
    return tuple(_CATALOG.values())


def register(key: str, document_class: type[Document]) -> None:
    """Add or replace a document; it takes precedence over the bundled ones.

    Call it at application startup, not per request. Replacing a bundled key (``gt.dpi``)
    changes validation for the whole process, including other libraries that use it.

    :raises ValueError: if the key does not look like ``country.document``.
    :raises TypeError: if the class does not implement the :class:`Document` protocol.
    """
    raw_key: object = key
    if (
        not isinstance(raw_key, str)
        or len(raw_key) > _MAX_KEY_LENGTH
        or _KEY.fullmatch(raw_key.lower()) is None
    ):
        message = "key must look like 'country.document' (a-z, 0-9 and _)"
        raise ValueError(message)
    candidate: object = document_class
    if not isinstance(candidate, type) or not issubclass(candidate, Document):
        message = f"{document_class!r} does not implement the Document protocol"
        raise TypeError(message)
    with _lock:
        _custom[key.lower()] = document_class


def _unregister(key: str) -> None:
    """Remove a registered document. For tests only."""
    with _lock:
        _custom.pop(key.lower(), None)
