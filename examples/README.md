# Examples

| File | What it shows | How to run it |
|------|---------------|---------------|
| `basic.py` | Validating, normalizing, `parse`, `generate` and the catalog, without a framework | `uv run python examples/basic.py` |
| `fastapi_app.py` | `Annotated` types with `Document(...)` in the request body, path and query | `uv run fastapi dev examples/fastapi_app.py` |
| `flask_app.py` | A JSON API using the core API and a WTForms form with `Document(...)` | `uv run flask --app examples/flask_app.py run` |
| `django_app.py` | `DocumentFormField` and `DocumentValidator` (models and DRF) | `uv run python examples/django_app.py runserver` |

`tests/test_examples.py` runs all four, so they always match the package.
