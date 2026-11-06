"""The examples in ``examples/`` work as written."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

EXAMPLES = Path(__file__).parents[1] / "examples"


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"examples_{name}", EXAMPLES / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Registered in sys.modules like a normal import (Pydantic resolves annotations there).
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_basic() -> None:
    result = subprocess.run(  # noqa: S603 - current interpreter and a repository script
        [sys.executable, str(EXAMPLES / "basic.py")], capture_output=True, text=True, check=True
    )
    assert "sv.dui: valid (12345678-4)" in result.stdout
    assert "sv.dui: the check digit does not match" in result.stdout
    assert "DPI compact: 1234567890101" in result.stdout
    assert "Check letter: N" in result.stdout


def test_fastapi() -> None:
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    client = TestClient(_load("fastapi_app").app)
    created = client.post("/customers", json={"name": "Ana", "dpi": "1234 56789 0101"})
    assert created.status_code == 201
    assert created.json()["dpi"] == "1234567890101"

    rejected = client.post("/customers", json={"name": "Ana", "dpi": "1234567880101"})
    assert rejected.status_code == 422
    assert rejected.json()["detail"][0]["type"] == "stdnum_checksum"

    assert client.post("/dui/format", json={"dui": "123456784"}).json() == {"dui": "12345678-4"}
    assert client.post("/validate", json={"key": "sv.dui", "number": "1"}).json() == {
        "valid": False,
        "error": "format",
    }
    assert client.post("/validate", json={"key": "xx.none", "number": "1"}).status_code == 404
    swapped = client.post("/validate", json={"key": "12345678-4", "number": "sv.dui"})
    assert swapped.status_code == 404
    assert "12345678" not in swapped.text


def test_flask() -> None:
    pytest.importorskip("flask")
    client = _load("flask_app").app.test_client()

    assert client.post("/api/customers", json={"dpi": "1234 56789 0101"}).get_json() == {
        "dpi": "1234567890101"
    }
    bad = client.post("/api/customers", json={"dpi": "1234567880101"})
    assert bad.status_code == 422
    assert bad.get_json() == {"field": "dpi", "error": "checksum"}
    assert client.post("/api/customers", json={}).status_code == 400

    ok = client.post("/form", data={"dpi": "1234 56789 0101", "cedula_pa": "pe 5 687"})
    assert ok.status_code == 201
    assert ok.get_json() == {"dpi": "1234567890101", "cedula_pa": "PE-5-687"}
    form_bad = client.post("/form", data={"dpi": "123"})
    assert form_bad.get_json() == {
        "errors": {"dpi": ["Does not match the format of this document."]}
    }


def test_django() -> None:
    pytest.importorskip("django")
    code = (
        "import sys, importlib.util;"
        f"spec = importlib.util.spec_from_file_location('django_app', {str(EXAMPLES / 'django_app.py')!r});"
        "m = importlib.util.module_from_spec(spec); sys.modules['django_app'] = m;"
        "spec.loader.exec_module(m);"
        "from django.test import Client; c = Client();"
        "r = c.post('/customers', {'name': 'Ana', 'dpi': '1234 56789 0101', 'cedula_ni': '0010101900001n'});"
        "print(r.status_code, r.content.decode());"
        "r = c.post('/customers', {'name': 'Ana', 'dpi': '1234567880101'});"
        "print(r.status_code, r.content.decode())"
    )
    # Separate process: the example configures Django and must not leak into other tests.
    result = subprocess.run(  # noqa: S603 - current interpreter and fixed code
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    created, rejected = result.stdout.strip().splitlines()
    assert created.startswith("201")
    assert '"dpi": "1234567890101"' in created
    assert '"cedula_ni": "001-010190-0001N"' in created
    assert rejected.startswith("422")
    assert "stdnum_checksum" in rejected
