"""WTForms and Flask-WTF integration.

Usage::

    from wtforms.validators import DataRequired
    from stdnum_centroamerica.contrib.wtforms import Document

    class CustomerForm(FlaskForm):
        dpi = StringField("DPI", validators=[DataRequired(), Document("gt.dpi")])

Empty fields are not validated: combine it with ``DataRequired`` or ``Optional``. With
``normalize="canonical"``, ``"compact"`` or ``"format"``, ``field.data`` is normalized after
validation.
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
    from wtforms import Field, Form
    from wtforms.validators import ValidationError
except ImportError as error:  # pragma: no cover - depends on the environment
    raise missing_dependency("WTForms>=3.1", "wtforms") from error

__all__ = ["Document"]


class Document:
    """WTForms validator for a document.

    :param key: document key, e.g. ``"gt.dpi"``.
    :param message: a single message for any error (otherwise, one per ``ErrorCode``).
    :param normalize: ``"none"`` (default, leaves ``field.data`` unchanged),
        ``"canonical"`` (the form to store; keeps Panama's hyphens), ``"compact"`` or
        ``"format"``.
    :param messages: messages per ``ErrorCode``.
    :param options: document options.
    """

    field_flags: Mapping[str, Any] = {}

    def __init__(
        self,
        key: str,
        message: str | None = None,
        *,
        normalize: Normalize = "none",
        messages: Mapping[ErrorCode, str] | None = None,
        **options: Any,
    ) -> None:
        check_normalize(normalize)
        self.key = key.lower()
        self.message = message
        self.normalize = normalize
        self._messages = {**MESSAGES, **(messages or {})}
        self._document = make(key, **options)

    def __call__(self, form: Form, field: Field) -> None:
        data = field.data
        if data is None or data == "":
            return
        value = str(data)
        error = self._document.validate(value).error
        if error is not None:
            raise ValidationError(self.message or field.gettext(self._messages[error]))
        field.data = normalized(self._document, value, self.normalize)
