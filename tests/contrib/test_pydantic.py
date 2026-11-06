"""Pydantic v2 and FastAPI integration."""

from __future__ import annotations

from typing import Annotated

import pytest

pydantic = pytest.importorskip("pydantic")

from pydantic import BaseModel, TypeAdapter, ValidationError  # noqa: E402

from stdnum_centroamerica import ErrorCode, UnknownDocumentError  # noqa: E402
from stdnum_centroamerica.contrib.pydantic import Document  # noqa: E402

Dpi = Annotated[str, Document("gt.dpi")]
CedulaNi = Annotated[str, Document("ni.cedula", normalize="format", strict_letter=True)]
CedulaPa = Annotated[str, Document("pa.cedula", normalize="format")]


class Customer(BaseModel):
    dpi: Dpi
    cedula: CedulaNi | None = None


def test_validates_and_normalizes() -> None:
    customer = Customer(dpi="1234 56789 0101", cedula="0010101900001n")
    assert customer.dpi == "1234567890101"
    assert customer.cedula == "001-010190-0001N"


def test_panama_keeps_the_hyphens() -> None:
    assert TypeAdapter(CedulaPa).validate_python(" pe 5 687 ") == "PE-5-687"


@pytest.mark.parametrize(
    ("value", "code"),
    [
        ("123", ErrorCode.FORMAT),
        ("1234567892301", ErrorCode.COMPONENT),
        ("1234567880101", ErrorCode.CHECKSUM),
    ],
)
def test_reports_the_reason_as_error_type(value: str, code: ErrorCode) -> None:
    with pytest.raises(ValidationError) as error:
        Customer(dpi=value)
    (detail,) = error.value.errors()
    assert detail["type"] == f"stdnum_{code.value}"
    assert detail["loc"] == ("dpi",)
    assert detail["ctx"] == {"document": "gt.dpi"}


def test_default_messages_are_english() -> None:
    with pytest.raises(ValidationError, match=r"The check digit does not match\."):
        Customer(dpi="1234567880101")


def test_document_options() -> None:
    with pytest.raises(ValidationError, match="stdnum_checksum"):
        Customer(dpi="1234567890101", cedula="001-010190-0001A")


def test_rejects_other_types() -> None:
    with pytest.raises(ValidationError, match="string_type"):
        Customer(dpi=1234567890101)  # type: ignore[arg-type]


def test_custom_messages_and_normalize_none() -> None:
    adapter = TypeAdapter(
        Annotated[
            str,
            Document(
                "sv.dui",
                normalize="none",
                messages={ErrorCode.CHECKSUM: "El dígito de control no coincide."},
            ),
        ]
    )
    assert adapter.validate_python("12345678-4") == "12345678-4"
    with pytest.raises(ValidationError, match=r"El dígito de control no coincide\."):
        adapter.validate_python("12345678-5")


def test_json_schema() -> None:
    schema = TypeAdapter(Dpi).json_schema()
    assert schema["type"] == "string"
    assert schema["x-stdnum-document"] == "gt.dpi"


def test_configuration_errors() -> None:
    with pytest.raises(UnknownDocumentError):
        Document("xx.none")
    with pytest.raises(ValueError, match="normalize"):
        Document("gt.dpi", normalize="other")  # type: ignore[arg-type]
    assert repr(Document("GT.DPI")) == "Document('gt.dpi', normalize='compact')"


def test_fastapi_responds_422() -> None:
    pytest.importorskip("fastapi")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.post("/customers")
    def create_customer(customer: Customer) -> Customer:
        return customer

    @app.get("/dui/{dui}")
    def get_dui(dui: Annotated[str, Document("sv.dui", normalize="format")]) -> dict[str, str]:
        return {"dui": dui}

    client = TestClient(app)
    ok = client.post("/customers", json={"dpi": "1234 56789 0101"})
    assert ok.status_code == 200
    assert ok.json()["dpi"] == "1234567890101"

    bad = client.post("/customers", json={"dpi": "1234567880101"})
    assert bad.status_code == 422
    assert bad.json()["detail"][0]["type"] == "stdnum_checksum"

    assert client.get("/dui/123456784").json() == {"dui": "12345678-4"}
    assert client.get("/dui/123456785").status_code == 422
