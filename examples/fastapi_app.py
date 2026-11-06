"""FastAPI app that validates documents in the request body.

Numbers travel in the body, never in the path or the query string: URLs end up in access
logs, browser history and ``Referer`` headers, and a document number is personal data.

Run:  uv run --with "fastapi[standard]" fastapi dev examples/fastapi_app.py
"""

from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

import stdnum_centroamerica as sca
from stdnum_centroamerica.contrib.pydantic import Document

# Reusable types: they validate and return the normalized number (canonical by default).
Dpi = Annotated[str, Document("gt.dpi")]
Dui = Annotated[str, Document("sv.dui", normalize="format")]
CedulaNi = Annotated[str, Document("ni.cedula", normalize="format", strict_letter=True)]


class CustomerIn(BaseModel):
    # Keeps the submitted number out of str(ValidationError), which often ends up in logs.
    model_config = ConfigDict(hide_input_in_errors=True)

    name: str
    dpi: Dpi
    cedula_ni: CedulaNi | None = None


class CustomerOut(CustomerIn):
    id: int


class DuiIn(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    dui: Dui


class ValidateIn(BaseModel):
    model_config = ConfigDict(hide_input_in_errors=True)

    key: str = Field(max_length=64, examples=["ni.cedula"])
    number: str = Field(max_length=sca.MAX_INPUT_LENGTH)


app = FastAPI(title="Customers")
_customers: dict[int, CustomerOut] = {}  # example only: an in-memory store, not thread-safe


@app.post("/customers", status_code=201)
def create_customer(customer: CustomerIn) -> CustomerOut:
    # An invalid DPI never gets here: FastAPI already answered 422 with type="stdnum_checksum".
    new = CustomerOut(id=len(_customers) + 1, **customer.model_dump())
    _customers[new.id] = new
    return new


@app.post("/dui/format")
def format_dui(body: DuiIn) -> dict[str, str]:
    return {"dui": body.dui}


@app.post("/validate")
def validate(body: ValidateIn) -> dict[str, object]:
    """Generic validation, e.g. for a dynamic frontend form."""
    try:
        result = sca.validate(body.key, body.number)
    except sca.UnknownDocumentError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return {"valid": result.is_valid, "error": result.error}
