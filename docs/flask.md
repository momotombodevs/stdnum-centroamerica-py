# Flask

Flask has no built-in validation, so there are two options: call the core API directly (JSON APIs), or use the WTForms validator (forms with Flask-WTF).

## JSON API, no extra dependencies

```bash
uv add stdnum-centroamerica
```

```python
from flask import Flask, request
import stdnum_centroamerica as sca

app = Flask(__name__)

@app.post("/api/customers")
def create_customer():
    data = request.get_json(silent=True) or {}
    dpi = data.get("dpi")
    if not isinstance(dpi, str):
        return {"field": "dpi", "error": "required"}, 400

    result = sca.validate("gt.dpi", dpi)
    if not result:
        return {"field": "dpi", "error": result.error}, 422     # "format" | "component" | "checksum"
    return {"dpi": sca.make("gt.dpi").compact(dpi)}, 201
```

Check the type before validating: `sca.validate()` raises `TypeError` for anything that is not a `str` (for example, a number in the JSON body).

## Forms with Flask-WTF

```bash
uv add "stdnum-centroamerica[wtforms]" flask-wtf
```

```python
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Optional
from stdnum_centroamerica.contrib.wtforms import Document

class CustomerForm(FlaskForm):
    dpi = StringField("DPI", validators=[DataRequired(), Document("gt.dpi", normalize="compact")])
    cedula = StringField(
        "Cédula", validators=[Optional(), Document("ni.cedula", "Invalid cédula", strict_letter=True)]
    )
```

| Parameter | Use |
|-----------|-----|
| `message` | a single message for any error |
| `messages` | one message per `ErrorCode` |
| `normalize` | `"none"` (default), `"canonical"` (the form to store; keeps Panama's hyphens), `"compact"` or `"format"`: leaves `field.data` normalized |
| document options | e.g. `strict_letter=True` |

Empty fields are not validated: combine `Document` with `DataRequired` or `Optional`. Messages default to English and go through `field.gettext`, so they are translated with your WTForms configuration; use `message=` or `messages=` to override them.

Complete, tested example: [examples/flask_app.py](../examples/flask_app.py).
