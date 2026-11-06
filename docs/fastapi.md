# FastAPI and Pydantic v2

```bash
uv add "stdnum-centroamerica[pydantic]"     # or: pip install "stdnum-centroamerica[pydantic]"
```

`Document(key, ...)` is metadata for `Annotated[str, ...]`. It validates the number and returns its normalized form. It works wherever Pydantic validates: models, FastAPI path and query parameters, `TypeAdapter`, SQLModel and Litestar.

## Reusable types

```python
from typing import Annotated
from stdnum_centroamerica.contrib.pydantic import Document

Dpi = Annotated[str, Document("gt.dpi")]                                  # "1234567890101"
Dui = Annotated[str, Document("sv.dui", normalize="format")]              # "12345678-4"
CedulaNi = Annotated[str, Document("ni.cedula", normalize="format", strict_letter=True)]
CedulaPa = Annotated[str, Document("pa.cedula", normalize="format")]      # Panama: always "format"
```

| Parameter | Values | Default |
|-----------|--------|---------|
| `normalize` | `"compact"` (for storage), `"format"` (for display), `"none"` (unchanged) | `"compact"` |
| `messages` | `{ErrorCode.CHECKSUM: "...", ...}` to translate or customize messages | English messages |
| document options | e.g. `strict_letter=True` | the document's defaults |

The key is checked when the module is imported: a misspelled key fails at startup, not on the first request.

## In a model and in routes

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Customer(BaseModel):
    name: str
    dpi: Dpi
    cedula: CedulaNi | None = None

app = FastAPI()

@app.post("/customers", status_code=201)
def create_customer(customer: Customer) -> Customer:
    return customer                      # customer.dpi is already compact

@app.get("/dui/{dui}")
def get_dui(dui: Dui) -> dict[str, str]:
    return {"dui": dui}
```

## Errors

An invalid number produces a Pydantic error with its own type, and FastAPI responds with 422:

```json
{
  "detail": [
    {
      "type": "stdnum_checksum",
      "loc": ["body", "dpi"],
      "msg": "The check digit does not match.",
      "input": "1234567880101",
      "ctx": {"document": "gt.dpi"}
    }
  ]
}
```

| `type` | Reason |
|--------|--------|
| `stdnum_format` | length, characters or structure |
| `stdnum_component` | a date, department, municipality or prefix that does not exist |
| `stdnum_checksum` | the check digit or letter does not match |

Frontends can rely on `type` to show their own message without depending on the text.

Messages default to English. Pass `messages=` to translate them, for example to Spanish:

```python
from stdnum_centroamerica import ErrorCode

Dpi = Annotated[str, Document("gt.dpi", messages={ErrorCode.CHECKSUM: "El dígito de control no coincide."})]
```

> The `input` field of the 422 response contains the submitted number, which is personal data. If you log validation errors, remove `input` before writing the log.

## Generic validation

For an endpoint that validates any document (for example, for a dynamic form), use the core API:

```python
import stdnum_centroamerica as sca
from fastapi import HTTPException, Query

@app.get("/validate")
def validate(key: str, number: Annotated[str, Query(max_length=sca.MAX_INPUT_LENGTH)]) -> dict[str, object]:
    try:
        result = sca.validate(key, number)
    except sca.UnknownDocumentError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return {"valid": result.is_valid, "error": result.error}
```

Complete, tested example: [examples/fastapi_app.py](../examples/fastapi_app.py).
