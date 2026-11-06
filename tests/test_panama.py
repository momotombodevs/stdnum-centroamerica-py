"""Panama cédula and RUC."""

from __future__ import annotations

import pytest

from stdnum_centroamerica.pa import Cedula, Ruc, normalize


def test_cedula_formats_with_hyphens_and_compacts_without_them() -> None:
    doc = Cedula()
    assert doc.format(" 8 926  1601 ") == "8-926-1601"
    assert doc.format("pe-5-687") == "PE-5-687"
    assert doc.format("8--926-1601") == "8-926-1601"
    # compact() strips separators, as everywhere else (volume/entry are lost).
    assert doc.compact("8-926-1601") == "89261601"


def test_ruc_compacts_and_formats() -> None:
    doc = Ruc()
    assert doc.format("8 nt 000 00") == "8-NT-000-00"
    assert doc.format("00023824 0930 212623") == "00023824-0930-212623"


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("\t8-926-1601\n", "8-926-1601"),
        ("8 - 926 - 1601", "8-926-1601"),
        ("8\f926\v1601", "8-926-1601"),
        ("\x008-926-1601\x00", "8-926-1601"),  # \0 is also stripped from both ends
        ("ñ-1-1", "ñ-1-1"),  # only ASCII letters are upper-cased
    ],
)
def test_normalize_cleans_separators(given: str, expected: str) -> None:
    assert normalize(given) == expected


def test_public_pattern_matches_the_normalized_form() -> None:
    assert Cedula.PATTERN.fullmatch("E-8-12345")
    assert not Cedula.PATTERN.fullmatch("E-8-12345\n")


def test_ruc_has_between_5_and_21_characters() -> None:
    assert Ruc().is_valid("1-1-1")  # 5 characters: the minimum
    assert not Ruc().is_valid("1-1")
    assert Ruc().is_valid("1234567890-12345-1234")  # 21 characters: the maximum
    assert not Ruc().is_valid("1234567890-123456-1234")  # 22: right shape, wrong length
