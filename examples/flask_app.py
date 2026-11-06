"""Flask app: direct validation in a JSON API and a WTForms form.

Run:  uv run flask --app examples/flask_app.py run
"""

from __future__ import annotations

from flask import Flask, request
from wtforms import Form, StringField
from wtforms.validators import DataRequired, Optional

import stdnum_centroamerica as sca
from stdnum_centroamerica.contrib.wtforms import Document

app = Flask(__name__)


@app.post("/api/customers")
def create_customer() -> tuple[dict[str, object], int]:
    """JSON API: uses the core API directly, no integration needed."""
    data = request.get_json(silent=True) or {}
    dpi = data.get("dpi")
    if not isinstance(dpi, str):
        return {"field": "dpi", "error": "required"}, 400

    result = sca.validate("gt.dpi", dpi)
    if not result:
        return {"field": "dpi", "error": result.error}, 422
    return {"dpi": sca.make("gt.dpi").compact(dpi)}, 201


class CustomerForm(Form):
    """With Flask-WTF, inherit from ``flask_wtf.FlaskForm`` instead of ``wtforms.Form``."""

    dpi = StringField("DPI", validators=[DataRequired(), Document("gt.dpi", normalize="compact")])
    cedula_pa = StringField(
        "Panama cédula", validators=[Optional(), Document("pa.cedula", normalize="format")]
    )


@app.post("/form")
def submit_form() -> tuple[dict[str, object], int]:
    form = CustomerForm(request.form)
    if not form.validate():
        return {"errors": form.errors}, 422
    return {"dpi": form.dpi.data, "cedula_pa": form.cedula_pa.data}, 201
