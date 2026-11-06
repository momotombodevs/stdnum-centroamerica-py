"""generate(), parse(), check digits and error reasons."""

from __future__ import annotations

import dataclasses
import datetime

import pytest

import stdnum_centroamerica as sca
from stdnum_centroamerica.gt import DpiData
from stdnum_centroamerica.hn import IdentidadData
from stdnum_centroamerica.mrz import MrzData
from stdnum_centroamerica.ni import Cedula as NiCedula
from stdnum_centroamerica.ni import CedulaData as NiCedulaData
from stdnum_centroamerica.pa import CedulaData as PaCedulaData
from stdnum_centroamerica.pa import CedulaKind

KEYS = [info.key for info in sca.describe()]
DIGITS = "0123456789"
TD3 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<L898902C36UTO7408122F1204159ZE184226B<<<<<10"
TD1 = "I<UTOD231458907<<<<<<<<<<<<<<<7408122F1204159UTO<<<<<<<<<<<6ERIKSSON<<ANNA<MARIA<<<<<<<<<<"
TD2 = "I<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<D231458907UTO7408122F1204159<<<<<<<6"

# -- generate ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", KEYS)
def test_generated_numbers_are_valid(key: str) -> None:
    document = sca.make(key)
    for _ in range(300):
        number = sca.generate(key)
        assert document.is_valid(number), f"{key} generated an invalid number"


@pytest.mark.parametrize("key", KEYS)
def test_generated_numbers_vary(key: str) -> None:
    assert len({sca.generate(key) for _ in range(30)}) > 1


def test_generated_check_digits_match_an_independent_computation() -> None:
    for _ in range(200):
        dui = sca.generate("sv.dui")
        total = sum(int(dui[pos]) * (9 - pos) for pos in range(8))
        assert (10 - total % 10) % 10 == int(dui[8])

        dpi = sca.generate("gt.dpi")
        total = sum(int(dpi[pos]) * (pos + 2) for pos in range(8))
        assert total % 11 == int(dpi[8])

        nit = sca.generate("gt.nit")
        body = nit[:-1]
        total = sum(int(body[len(body) - 1 - pos]) * (pos + 2) for pos in range(len(body)))
        check = (11 - total % 11) % 11
        assert nit[-1] == ("K" if check == 10 else str(check))


class _SinGenerador:
    def is_valid(self, number: str) -> bool:
        return True

    def validate(self, number: str) -> sca.ValidationResult:
        return sca.ValidationResult()

    def format(self, number: str) -> str:
        return number

    def compact(self, number: str) -> str:
        return number


@pytest.mark.usefixtures("clean_registry")
def test_document_without_generate_or_parse_raises() -> None:
    sca.register("xx.sin_generador", _SinGenerador)
    with pytest.raises(sca.UnsupportedOperationError, match="does not generate"):
        sca.generate("xx.sin_generador")
    with pytest.raises(sca.UnsupportedOperationError, match="no components"):
        sca.parse("xx.sin_generador", "1")


# -- check digits -----------------------------------------------------------------------

PROTECTED = [
    ("gt.nit", "36029785", range(7), DIGITS),
    ("gt.nit", "36029785", [7], DIGITS + "K"),
    ("gt.dpi", "1234567890101", range(8), DIGITS),
    ("gt.dpi", "1234567890101", [8], DIGITS),
    ("sv.dui", "123456784", [8], DIGITS),
    ("sv.nit", "06141303861364", [13], DIGITS),
    ("sv.nit", "07162002610014", [13], DIGITS),
    ("mrz.td3", TD3, range(57, 64), DIGITS),
    ("mrz.td3", TD3, range(65, 72), DIGITS),
    ("mrz.td3", TD3, [53, 63, 71, 86, 87], DIGITS),
    ("mrz.td1", TD1, [*range(30, 37), *range(38, 45), 59], DIGITS),
    ("mrz.td2", TD2, [*range(49, 56), *range(57, 64), 71], DIGITS),
    ("ni.cedula", "0010101900001N", [13], "ABCDEFGHJKLMNPQRSTUVWXY"),
]


@pytest.mark.parametrize(("key", "number", "positions", "alphabet"), PROTECTED)
def test_any_change_to_a_protected_character_invalidates_the_number(
    key: str, number: str, positions: range | list[int], alphabet: str
) -> None:
    # The Nicaraguan cédula letter is only checked in strict mode.
    options = {"strict_letter": True} if key == "ni.cedula" else {}
    assert sca.is_valid(key, number, **options), "the base number must be valid"

    for position in positions:
        for replacement in alphabet:
            if replacement == number[position]:
                continue
            mutated = number[:position] + replacement + number[position + 1 :]
            assert not sca.is_valid(key, mutated, **options), f"{key} accepted {mutated}"


# -- error reasons ----------------------------------------------------------------------

ERRORS = [
    ("gt.nit", "", sca.ErrorCode.FORMAT),
    ("gt.nit", "1234567-0", sca.ErrorCode.CHECKSUM),
    ("gt.dpi", "2000 0000 A 0101", sca.ErrorCode.FORMAT),
    ("gt.dpi", "2000000000023", sca.ErrorCode.COMPONENT),
    ("sv.dui", "00000000-1", sca.ErrorCode.CHECKSUM),
    ("sv.nit", "12345", sca.ErrorCode.FORMAT),
    ("sv.nit", "00000000-1", sca.ErrorCode.CHECKSUM),
    ("hn.identidad", "0801-1990", sca.ErrorCode.FORMAT),
    ("hn.identidad", "0899199000001", sca.ErrorCode.COMPONENT),
    ("ni.cedula", "001-010190-00001", sca.ErrorCode.FORMAT),
    ("ni.cedula", "001-320190-0001N", sca.ErrorCode.COMPONENT),
    ("ni.ruc", "0000300766011M", sca.ErrorCode.COMPONENT),
    ("ni.ruc", "X", sca.ErrorCode.FORMAT),
    ("pa.cedula", "ABC", sca.ErrorCode.FORMAT),
    ("pa.ruc", "1", sca.ErrorCode.FORMAT),
    ("cr.dimex", "0123", sca.ErrorCode.FORMAT),
]


@pytest.mark.parametrize(("key", "number", "expected"), ERRORS)
def test_reports_the_failure_reason(key: str, number: str, expected: sca.ErrorCode) -> None:
    result = sca.validate(key, number)
    assert not result.is_valid
    assert result.error is expected


def test_validate_accepts_options() -> None:
    assert sca.validate("ni.cedula", "001-010190-0001A").error is None
    result = sca.validate("ni.cedula", "001-010190-0001A", strict_letter=True)
    assert result.error is sca.ErrorCode.CHECKSUM


def test_results_are_immutable_values() -> None:
    result = sca.validate("sv.dui", "12345678-5")
    assert result == sca.ValidationResult(sca.ErrorCode.CHECKSUM)
    assert result.error == "checksum"  # StrEnum: serializes as text
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.error = None  # type: ignore[misc]


# -- parse ------------------------------------------------------------------------------


def test_nicaragua_cedula() -> None:
    data = sca.parse("ni.cedula", "001-010190-0001n")
    assert data == NiCedulaData(
        municipality_code=1,
        birth_day=1,
        birth_month=1,
        birth_year_two_digits=90,
        sequence="0001",
        letter="N",
    )
    assert not data.is_born_abroad()
    assert "birth" not in repr(data)
    assert "0001" not in repr(data)


def test_cedula_century_is_offered_as_candidates() -> None:
    data = sca.parse("ni.cedula", "001-010190-0001N")
    assert data.birth_year_candidates(datetime.date(2026, 10, 20)) == (1990,)
    assert data.birth_year_candidates(datetime.date(2100, 12, 31)) == (1990, 2090)

    recent = sca.parse("ni.cedula", "001-150620-0001A")
    assert recent.birth_year_candidates(datetime.date(2026, 10, 20)) == (1920, 2020)


def test_candidate_with_a_future_date_in_the_same_year_is_dropped() -> None:
    recent = sca.parse("ni.cedula", "001-150620-0001A")
    assert recent.birth_year_candidates(datetime.date(2020, 1, 1)) == (1920,)
    assert recent.birth_year_candidates(datetime.date(2020, 6, 15)) == (1920, 2020)


def test_candidates_use_today_by_default(freeze_today: object) -> None:
    freeze_today(datetime.date(2020, 1, 1))  # type: ignore[operator]
    assert sca.parse("ni.cedula", "001-150620-0001A").birth_year_candidates() == (1920,)


def test_candidates_may_be_empty() -> None:
    # 29/02/01 exists neither in 1901 nor in 2001
    data = sca.parse("ni.cedula", "001-290201-0001A")
    assert data.birth_year_candidates(datetime.date(2026, 10, 20)) == ()


def test_february_29_drops_non_leap_years() -> None:
    data = sca.parse("ni.cedula", "001-290200-0001A")
    assert data.birth_year_candidates(datetime.date(2026, 10, 20)) == (
        2000,
    )  # 1900 was not a leap year


def test_cedula_honors_strict_municipality() -> None:
    assert sca.parse("ni.cedula", "282-010190-0001A") is not None
    assert sca.parse("ni.cedula", "282-010190-0001A", strict_municipality=True) is None


def test_nicaragua_cedula_born_abroad() -> None:
    digits = "8880101900001"
    data = sca.parse("ni.cedula", digits + NiCedula.check_letter(digits))
    assert data.municipality_code == 888
    assert data.is_born_abroad()


def test_honduras_identidad() -> None:
    data = sca.parse("hn.identidad", "0906-1990-00001")
    assert data == IdentidadData(9, 6, 1990, "00001", None)


def test_honduras_identidad_with_special_code() -> None:
    data = sca.parse("hn.identidad", "0890-2010-00012")
    assert data == IdentidadData(None, None, 2010, "00012", "0890")


def test_guatemala_dpi() -> None:
    assert sca.parse("gt.dpi", "1234 56789 0101") == DpiData("12345678", 1, 1)


def test_panama_cedula() -> None:
    assert sca.parse("pa.cedula", "8-926-1601") == PaCedulaData(
        CedulaKind.BIRTH, 8, None, "926", "1601"
    )
    assert sca.parse("pa.cedula", "pe 5 687") == PaCedulaData(
        CedulaKind.BORN_ABROAD, None, None, "5", "687"
    )
    assert sca.parse("pa.cedula", "N-19-473") == PaCedulaData(
        CedulaKind.NATURALIZED, None, None, "19", "473"
    )
    assert sca.parse("pa.cedula", "E-8-12345") == PaCedulaData(
        CedulaKind.FOREIGN_RESIDENT, 8, None, None, "12345"
    )
    assert sca.parse("pa.cedula", "3-PI-12-345") == PaCedulaData(
        CedulaKind.BIRTH, 3, "PI", "12", "345"
    )


def test_passport_mrz() -> None:
    data = sca.parse("mrz.td3", TD3)
    assert isinstance(data, MrzData)
    assert data.surname == "ERIKSSON"
    assert data.document_number == "L898902C3"
    assert sca.parse("mrz.td3", "P<UTO") is None


def test_invalid_number_returns_none() -> None:
    assert sca.parse("ni.cedula", "001-010190-0001A", strict_letter=True) is None
    assert sca.parse("hn.identidad", "0899-1990-00001") is None
    assert sca.parse("gt.dpi", "1234567880101") is None
    assert sca.parse("pa.cedula", "ABC") is None


def test_document_without_components_raises() -> None:
    with pytest.raises(sca.UnsupportedOperationError):
        sca.parse("gt.nit", "1234567-9")


@pytest.mark.parametrize(
    "key", [key for key in KEYS if isinstance(sca.make(key), sca.SupportsParse)]
)
def test_generated_numbers_can_be_parsed(key: str) -> None:
    for _ in range(100):
        assert sca.parse(key, sca.generate(key)) is not None


def test_data_can_be_serialized() -> None:
    data = sca.parse("pa.cedula", "8-926-1601")
    assert dataclasses.asdict(data) == {
        "kind": "birth",
        "province_code": 8,
        "suffix": None,
        "volume": "926",
        "entry": "1601",
    }
