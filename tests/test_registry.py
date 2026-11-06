"""Public API: make, validate, is_valid, keys, describe and register."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import stdnum_centroamerica as sca
from stdnum_centroamerica.cr import Nite
from stdnum_centroamerica.gt import Nit

COUNTRIES = {
    "GT": "Guatemala",
    "SV": "El Salvador",
    "HN": "Honduras",
    "NI": "Nicaragua",
    "CR": "Costa Rica",
    "PA": "Panama",
    "ICAO": "International",
}


def test_resolves_documents_by_key() -> None:
    assert isinstance(sca.make("GT.NIT"), Nit)
    assert sca.is_valid("sv.dui", "12345678-4")
    assert not sca.is_valid("sv.dui", "12345678-5")
    assert sca.is_valid("pa.cedula", "8-926-1601")


def test_every_key_can_be_instantiated() -> None:
    for key in sca.keys():  # noqa: SIM118 - a function, not a dict
        assert isinstance(sca.make(key), sca.Document), key


def test_make_reuses_instances() -> None:
    assert sca.make("ni.cedula") is sca.make("NI.CEDULA")
    assert sca.make("ni.cedula", strict_letter=True) is sca.make("ni.cedula", strict_letter=True)
    assert sca.make("ni.cedula") is not sca.make("ni.cedula", strict_letter=True)


def test_options_reach_the_document_constructor() -> None:
    # 001-010190-0001A has the wrong letter (the right one is N).
    assert sca.is_valid("ni.cedula", "001-010190-0001A")
    assert not sca.is_valid("ni.cedula", "001-010190-0001A", strict_letter=True)
    assert not sca.is_valid("ni.cedula", "282-010190-0001N", strict_municipality=True)


def test_unknown_option_raises_type_error() -> None:
    with pytest.raises(TypeError):
        sca.make("ni.cedula", strictLetter=True)
    with pytest.raises(TypeError):
        sca.make("gt.nit", strict_letter=True)


def test_unhashable_options_create_a_new_instance() -> None:
    from stdnum_centroamerica.ni import Cedula

    class UnhashableCedula(Cedula):
        __slots__ = ()
        __hash__ = None  # type: ignore[assignment]

    cedula = UnhashableCedula(strict_letter=True)
    first = sca.make("ni.ruc", cedula=cedula)
    assert first is not sca.make("ni.ruc", cedula=cedula)
    assert not first.is_valid("001-010190-0001A")


def test_describe_lists_bundled_documents() -> None:
    info = sca.describe()
    assert len(info) == 18
    assert info[0] == sca.DocumentInfo("gt.nit", Nit, "GT", "NIT", sca.Level.COMPLETE)


def test_describe_matches_the_readme_table() -> None:
    readme = (Path(__file__).parents[1] / "README.md").read_text(encoding="utf-8")
    rows = re.findall(
        r"^\| ([^|]+) \| ([^|]+) \| `([a-z]+\.[a-z0-9_]+)` \| (complete|format)",
        readme,
        re.MULTILINE,
    )
    expected = {
        key: (country, name, sca.Level.COMPLETE if level == "complete" else sca.Level.FORMAT)
        for country, name, key, level in rows
    }
    actual = {info.key: (COUNTRIES[info.country], info.name, info.level) for info in sca.describe()}
    assert actual == expected


def test_unknown_key_raises_with_suggestions() -> None:
    with pytest.raises(sca.UnknownDocumentError, match="Unsupported document"):
        sca.make("xx.nada")
    with pytest.raises(LookupError, match=r"ni\.cedula"):
        sca.make("ni.cedla")


def test_key_must_be_str() -> None:
    with pytest.raises(TypeError, match="key must be a str"):
        sca.make(None)  # type: ignore[arg-type]


@pytest.mark.usefixtures("clean_registry")
def test_register_replaces_a_document_and_requires_the_protocol() -> None:
    sca.register("XX.NITE", Nite)
    assert isinstance(sca.make("xx.nite"), Nite)
    assert sca.keys()[0] == "xx.nite"

    sca.register("gt.nit", Nite)  # replaces a bundled one
    assert isinstance(sca.make("gt.nit"), Nite)
    assert sca.keys().count("gt.nit") == 1

    with pytest.raises(TypeError, match="Document protocol"):
        sca.register("xx.mal", object)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Document protocol"):
        sca.register("xx.mal", Nite())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match=r"country\.document"):
        sca.register("sin_punto", Nite)
    with pytest.raises(ValueError, match=r"country\.document"):
        sca.register("xx." + "a" * 100, Nite)


def test_version() -> None:
    pyproject = (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{sca.__version__}"' in pyproject


def test_importing_the_package_imports_no_framework() -> None:
    import subprocess
    import sys

    code = (
        "import sys, stdnum_centroamerica as s; s.is_valid('sv.dui', '12345678-4');"
        "bad = [m for m in ('pydantic', 'django', 'wtforms', 'flask', 'fastapi')"
        " if m in sys.modules]; print(bad)"
    )
    result = subprocess.run(  # noqa: S603 - current interpreter, fixed code
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "[]"
