"""FastAPI app that validates documents in the body, the path and the query string.

Run:  uv run fastapi dev examples/fastapi_app.py
      (or: uv run uvicorn examples.fastapi_app:app --reload)
"""

from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

import stdnum_centroamerica as sca
from stdnum_centroamerica.contrib.pydantic import Document

# Reusable types: they validate and return the normalized number.
Dpi = Annotated[str, Document("gt.dpi")]
Dui = Annotated[str, Document("sv.dui", normalize="format")]
CedulaNi = Annotated[str, Document("ni.cedula", normalize="format", strict_letter=True)]


class CustomerIn(BaseModel):
    name: str
    dpi: Dpi
    cedula_ni: CedulaNi | None = None


class CustomerOut(CustomerIn):
    id: int


app = FastAPI(title="Customers")
_customers: dict[int, CustomerOut] = {}


@app.post("/customers", status_code=201)
def create_customer(customer: CustomerIn) -> CustomerOut:
    # An invalid DPI never gets here: FastAPI already answered 422 with type="stdnum_checksum".
    new = CustomerOut(id=len(_customers) + 1, **customer.model_dump())
    _customers[new.id] = new
    return new


@app.get("/dui/{dui}")
def get_dui(dui: Dui) -> dict[str, str]:
    return {"dui": dui}


@app.get("/validate")
def validate(
    key: Annotated[str, Query(examples=["ni.cedula"])],
    number: Annotated[str, Query(max_length=sca.MAX_INPUT_LENGTH)],
) -> dict[str, object]:
    """Generic validation, e.g. for a dynamic frontend form."""
    try:
        result = sca.validate(key, number)
    except sca.UnknownDocumentError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return {"valid": result.is_valid, "error": result.error}
