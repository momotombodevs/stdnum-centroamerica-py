"""Common instance behavior: equality, hash, copy, pickle and repr."""

from __future__ import annotations

import copy
import pickle

import pytest

import stdnum_centroamerica as sca
from stdnum_centroamerica.contrib._common import missing_dependency
from stdnum_centroamerica.ni import Cedula, Ruc
from stdnum_centroamerica.sv import Dui, Nit


@pytest.mark.parametrize("key", [info.key for info in sca.describe()])
def test_pickle_and_deepcopy_keep_options(key: str) -> None:
    document = sca.make(key)
    for clone in (pickle.loads(pickle.dumps(document)), copy.deepcopy(document)):  # noqa: S301
        assert clone == document
        assert type(clone) is type(document)


def test_equality_and_hash_follow_options() -> None:
    assert Cedula(strict_letter=True) == Cedula(strict_letter=True)
    assert Cedula(strict_letter=True) != Cedula()
    assert len({Cedula(), Cedula(), Cedula(strict_letter=True)}) == 2
    assert Ruc(cedula=Cedula(strict_letter=True)) == Ruc(cedula=Cedula(strict_letter=True))
    assert Nit(dui=Dui()) == Nit()
    assert Dui() != Nit()
    assert Dui() != "sv.dui"


def test_pickle_document_with_a_nested_document() -> None:
    ruc = Ruc(cedula=Cedula(strict_letter=True))
    clone = pickle.loads(pickle.dumps(ruc))  # noqa: S301 - object created by the test
    assert not clone.is_valid("001-010190-0001A")


def test_repr_shows_options() -> None:
    assert repr(Dui()) == "Dui()"
    assert repr(Nit()) == "Nit(dui=Dui())"
    assert repr(Ruc()) == "Ruc(cedula=Cedula(strict_municipality=False, strict_letter=False))"


def test_base_document_without_pattern_cannot_validate() -> None:
    with pytest.raises(NotImplementedError):
        sca.BaseDocument().is_valid("1")


def test_message_when_an_integration_is_missing() -> None:
    error = missing_dependency("Django>=4.2", "django")
    assert isinstance(error, ImportError)
    assert 'pip install "stdnum-centroamerica[django]"' in str(error)
    assert 'uv add "stdnum-centroamerica[django]"' in str(error)
