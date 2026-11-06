"""Django and Django REST Framework integration.

In a model::

    from stdnum_centroamerica.contrib.django import DocumentValidator

    class Customer(models.Model):
        dpi = models.CharField(max_length=13, validators=[DocumentValidator("gt.dpi")])

In a form, :class:`DocumentFormField` also returns the normalized number::

    class CustomerForm(forms.Form):
        dpi = DocumentFormField("gt.dpi")

DRF accepts Django validators as they are::

    dpi = serializers.CharField(validators=[DocumentValidator("gt.dpi")])

Messages are marked with ``gettext_lazy``, so projects can translate them in their own
catalogs. The error ``code`` is ``stdnum_format``, ``stdnum_component`` or
``stdnum_checksum``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from stdnum_centroamerica._registry import make
from stdnum_centroamerica._types import ErrorCode
from stdnum_centroamerica.contrib._common import (
    Normalize,
    check_normalize,
    missing_dependency,
    normalized,
)

try:
    from django import forms
    from django.core.exceptions import ValidationError
    from django.utils.deconstruct import deconstructible
    from django.utils.functional import Promise
    from django.utils.translation import gettext_lazy as _
except ImportError as error:  # pragma: no cover - depends on the environment
    raise missing_dependency("Django>=4.2", "django") from error

if TYPE_CHECKING:
    from django.utils.functional import _StrPromise as StrPromise
else:
    StrPromise = Promise

__all__ = ["DocumentFormField", "DocumentValidator"]

MESSAGES: Mapping[ErrorCode, str | StrPromise] = {
    ErrorCode.FORMAT: _("Does not match the format of this document."),
    ErrorCode.COMPONENT: _("Contains a date or code that does not exist."),
    ErrorCode.CHECKSUM: _("The check digit does not match."),
}


@deconstructible(path="stdnum_centroamerica.contrib.django.DocumentValidator")
class DocumentValidator:
    """Django validator for a document.

    It is deconstructible: it can be used in models and migrations serialize it. For that
    reason, options must be plain values (``strict_letter=True``), not instances.

    :param key: document key, e.g. ``"gt.dpi"``.
    :param message: a single message for any error (otherwise, one per ``ErrorCode``).
    :param options: document options.
    """

    def __init__(self, key: str, message: str | StrPromise | None = None, **options: Any) -> None:
        self.key = key.lower()
        self.message = message
        self.options = options
        self._document = make(key, **options)

    def __call__(self, value: object) -> None:
        if value is None:
            return
        error = self._document.validate(str(value)).error
        if error is not None:
            raise ValidationError(
                self.message or MESSAGES[error],
                code=f"stdnum_{error.value}",
                params={"document": self.key},  # never the number: it is personal data
            )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DocumentValidator) and (self.key, self.message, self.options) == (
            other.key,
            other.message,
            other.options,
        )

    def __hash__(self) -> int:
        return hash((self.key, self.message, tuple(sorted(self.options.items()))))


class DocumentFormField(forms.CharField):
    """Form field that validates the document and returns the normalized number.

    :param key: document key.
    :param normalize: ``"canonical"`` (default: the form to store, compact except for
        Panama, whose hyphens are part of the number), ``"compact"``, ``"format"`` or
        ``"none"``.
    :param document_options: document options, e.g. ``{"strict_letter": True}``.
    :param kwargs: ``CharField`` arguments (``required``, ``label``, ...).
    """

    def __init__(
        self,
        key: str,
        *,
        normalize: Normalize = "canonical",
        document_options: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        check_normalize(normalize)
        self.document_key = key.lower()
        self.normalize = normalize
        options = dict(document_options or {})
        self._document = make(key, **options)
        kwargs.setdefault("max_length", 128)
        super().__init__(**kwargs)
        self.validators.append(DocumentValidator(key, **options))

    def clean(self, value: Any) -> Any:
        cleaned = super().clean(value)
        if cleaned in self.empty_values:
            return cleaned
        return normalized(self._document, cleaned, self.normalize)
