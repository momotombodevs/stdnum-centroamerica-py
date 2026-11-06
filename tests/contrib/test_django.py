"""Django integration (model validator, form field and DRF)."""

from __future__ import annotations

import pytest

pytest.importorskip("django")

import django
from django.conf import settings

from tests.contrib import django_settings

if not settings.configured:
    settings.configure(
        **{
            name: getattr(django_settings, name)
            for name in (
                "SECRET_KEY",
                "INSTALLED_APPS",
                "DATABASES",
                "USE_I18N",
                "LANGUAGE_CODE",
                "USE_TZ",
            )
        }
    )
    django.setup()

from django import forms
from django.core.exceptions import ValidationError
from django.db.migrations.writer import MigrationWriter

from stdnum_centroamerica.contrib.django import DocumentFormField, DocumentValidator


def test_validator_accepts_valid_and_ignores_none() -> None:
    validator = DocumentValidator("gt.dpi")
    validator("1234 56789 0101")
    validator(None)


@pytest.mark.parametrize(
    ("value", "code"),
    [
        ("123", "stdnum_format"),
        ("1234567892301", "stdnum_component"),
        ("1234567880101", "stdnum_checksum"),
    ],
)
def test_validator_reports_the_reason(value: str, code: str) -> None:
    with pytest.raises(ValidationError) as error:
        DocumentValidator("gt.dpi")(value)
    assert error.value.code == code
    assert "1234" not in str(error.value.params)  # never the number


def test_single_message_and_options() -> None:
    validator = DocumentValidator("ni.cedula", message="Invalid cédula", strict_letter=True)
    with pytest.raises(ValidationError, match="Invalid cédula"):
        validator("001-010190-0001A")
    DocumentValidator("ni.cedula")("001-010190-0001A")


def test_validator_serializes_in_migrations() -> None:
    validator = DocumentValidator("ni.cedula", strict_letter=True)
    path, args, kwargs = validator.deconstruct()  # type: ignore[attr-defined]
    assert path == "stdnum_centroamerica.contrib.django.DocumentValidator"
    assert args == ("ni.cedula",)
    assert kwargs == {"strict_letter": True}
    serialized, _imports = MigrationWriter.serialize(validator)
    assert "DocumentValidator('ni.cedula', strict_letter=True)" in serialized
    assert validator == DocumentValidator("NI.CEDULA", strict_letter=True)
    assert validator != DocumentValidator("ni.cedula")
    assert len({validator, DocumentValidator("ni.cedula", strict_letter=True)}) == 1


class CustomerForm(forms.Form):
    dpi = DocumentFormField("gt.dpi")
    cedula_pa = DocumentFormField("pa.cedula", normalize="format", required=False)
    cedula_ni = DocumentFormField(
        "ni.cedula", normalize="none", document_options={"strict_letter": True}, required=False
    )


def test_form_field_validates_and_normalizes() -> None:
    form = CustomerForm(data={"dpi": "1234 56789 0101", "cedula_pa": "pe 5 687", "cedula_ni": ""})
    assert form.is_valid(), form.errors
    assert form.cleaned_data == {"dpi": "1234567890101", "cedula_pa": "PE-5-687", "cedula_ni": ""}


def test_form_field_shows_the_error() -> None:
    form = CustomerForm(data={"dpi": "1234567880101", "cedula_ni": "001-010190-0001A"})
    assert not form.is_valid()
    assert form.errors["dpi"] == ["The check digit does not match."]
    assert form.has_error("cedula_ni", code="stdnum_checksum")


def test_invalid_normalize() -> None:
    with pytest.raises(ValueError, match="normalize"):
        DocumentFormField("gt.dpi", normalize="other")  # type: ignore[arg-type]
