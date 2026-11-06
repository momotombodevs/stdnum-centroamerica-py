"""WTForms integration (and therefore Flask-WTF)."""

from __future__ import annotations

import pytest

pytest.importorskip("wtforms")

from wtforms import Form, StringField
from wtforms.validators import DataRequired, Optional

from stdnum_centroamerica import ErrorCode
from stdnum_centroamerica.contrib.wtforms import Document


class PostData(dict[str, str]):
    """POST data, as Flask-WTF passes it."""

    def getlist(self, key: str) -> list[str]:
        return [self[key]] if key in self else []


class CustomerForm(Form):
    dpi = StringField("DPI", validators=[DataRequired(), Document("gt.dpi", normalize="compact")])
    cedula = StringField(
        "Cédula",
        validators=[Optional(), Document("ni.cedula", "Invalid cédula", strict_letter=True)],
    )
    dui = StringField(
        "DUI",
        validators=[Optional(), Document("sv.dui", messages={ErrorCode.CHECKSUM: "Bad DUI"})],
    )


def test_validates_and_normalizes() -> None:
    form = CustomerForm(PostData(dpi="1234 56789 0101", cedula="001-010190-0001N", dui=""))
    assert form.validate(), form.errors
    assert form.dpi.data == "1234567890101"
    assert form.cedula.data == "001-010190-0001N"  # normalize="none" by default


def test_reports_errors() -> None:
    form = CustomerForm(PostData(dpi="1234567880101", cedula="001-010190-0001A", dui="12345678-5"))
    assert not form.validate()
    assert form.errors == {
        "dpi": ["The check digit does not match."],
        "cedula": ["Invalid cédula"],
        "dui": ["Bad DUI"],
    }


def test_empty_field_is_left_to_data_required() -> None:
    form = CustomerForm(PostData(dpi=""))
    assert not form.validate()
    assert form.errors["dpi"] == ["This field is required."]


def test_invalid_normalize() -> None:
    with pytest.raises(ValueError, match="normalize"):
        Document("gt.dpi", normalize="other")  # type: ignore[arg-type]


def test_without_data_required_an_empty_field_is_not_validated() -> None:
    class OptionalForm(Form):
        dpi = StringField("DPI", validators=[Document("gt.dpi")])

    assert OptionalForm(PostData(dpi="")).validate()
    assert OptionalForm(PostData()).validate()
