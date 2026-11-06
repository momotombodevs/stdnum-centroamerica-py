"""Pydantic v2 integration (FastAPI, SQLModel, Litestar).

Usage::

    from typing import Annotated
    from pydantic import BaseModel
    from stdnum_centroamerica.contrib.pydantic import Document

    Dpi = Annotated[str, Document("gt.dpi")]

    class Customer(BaseModel):
        dpi: Dpi                                                     # stored compact
        cedula: Annotated[str, Document("ni.cedula", normalize="format", strict_letter=True)]

An invalid number raises a Pydantic ``ValidationError`` of type ``stdnum_format``,
``stdnum_component`` or ``stdnum_checksum``; FastAPI responds with 422.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from stdnum_centroamerica._registry import make
from stdnum_centroamerica._types import ErrorCode
from stdnum_centroamerica.contrib._common import (
    MESSAGES,
    Normalize,
    check_normalize,
    missing_dependency,
    normalized,
)

try:
    from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
    from pydantic.json_schema import JsonSchemaValue
    from pydantic_core import CoreSchema, PydanticCustomError, core_schema
except ImportError as error:  # pragma: no cover - depends on the environment
    raise missing_dependency("pydantic>=2.6", "pydantic") from error

__all__ = ["Document"]


class Document:
    """``Annotated[str, ...]`` metadata that validates and normalizes a document.

    :param key: document key, e.g. ``"gt.dpi"``.
    :param normalize: ``"compact"`` (default), ``"format"`` or ``"none"``.
    :param messages: messages per ``ErrorCode``, to translate or customize them.
    :param options: document options, e.g. ``strict_letter=True``.
    """

    __slots__ = ("_document", "_messages", "key", "normalize")

    def __init__(
        self,
        key: str,
        *,
        normalize: Normalize = "compact",
        messages: Mapping[ErrorCode, str] | None = None,
        **options: Any,
    ) -> None:
        check_normalize(normalize)
        self.key = key.lower()
        self.normalize = normalize
        self._document = make(key, **options)  # fails at import time if the key is unknown
        self._messages = {**MESSAGES, **(messages or {})}

    def __repr__(self) -> str:
        return f"Document({self.key!r}, normalize={self.normalize!r})"

    def _validate(self, value: str) -> str:
        error = self._document.validate(value).error
        if error is not None:
            raise PydanticCustomError(
                f"stdnum_{error.value}", self._messages[error], {"document": self.key}
            )
        return normalized(self._document, value, self.normalize)

    def __get_pydantic_core_schema__(
        self, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(self._validate, handler(source_type))

    def __get_pydantic_json_schema__(
        self, schema: CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(schema)
        json_schema.setdefault("description", f"Document {self.key}")
        json_schema["x-stdnum-document"] = self.key
        return json_schema
