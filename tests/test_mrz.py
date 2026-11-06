"""ICAO Doc 9303 MRZs."""

from __future__ import annotations

import pytest

from stdnum_centroamerica import ErrorCode
from stdnum_centroamerica.mrz import MrzData, Td1, Td2, Td3, check_digit

TD3 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\nL898902C36UTO7408122F1204159ZE184226B<<<<<10"
TD1 = (
    "I<UTOD231458907<<<<<<<<<<<<<<<\n7408122F1204159UTO<<<<<<<<<<<6\nERIKSSON<<ANNA<MARIA<<<<<<<<<<"
)
TD2 = "I<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<\nD231458907UTO7408122F1204159<<<<<<<6"


def test_check_digit_follows_the_specification() -> None:
    # ICAO 9303 example: L898902C3 -> 6
    assert check_digit("L898902C3") == 6
    assert check_digit("740812") == 2
    assert check_digit("<<<<<<") == 0
    assert Td3.check_digit("L898902C3") == 6


@pytest.mark.parametrize("value", ["l898902c3", "ABC-1", "\u00d1", "\u0661"])
def test_check_digit_rejects_characters_outside_the_alphabet(value: str) -> None:
    with pytest.raises(ValueError, match="A-Z, 0-9 and <"):
        check_digit(value)


def test_parse_passport() -> None:
    data = Td3().parse(TD3)
    assert data == MrzData(
        document_code="P",
        issuing_state="UTO",
        surname="ERIKSSON",
        given_names="ANNA MARIA",
        document_number="L898902C3",
        nationality="UTO",
        birth_date="740812",
        sex="F",
        expiry_date="120415",
        optional_data="ZE184226B",
    )


def test_data_repr_hides_personal_data() -> None:
    text = repr(Td3().parse(TD3))
    for secret in ("ERIKSSON", "ANNA", "L898902C3", "740812", "120415", "ZE184226B"):
        assert secret not in text


def test_parse_td1_and_td2_id_cards() -> None:
    td1 = Td1().parse(TD1)
    assert td1 is not None
    assert td1.document_number == "D23145890"
    assert td1.surname == "ERIKSSON"
    assert td1.given_names == "ANNA MARIA"
    assert td1.expiry_date == "120415"

    td2 = Td2().parse(TD2)
    assert td2 is not None
    assert td2.document_number == "D23145890"
    assert td2.surname == "ERIKSSON"
    assert td2.birth_date == "740812"


def test_parse_invalid_mrz_returns_none() -> None:
    assert Td3().parse(TD3.replace("C36", "C37")) is None
    assert Td3().parse("") is None


def test_error_reasons() -> None:
    td3 = Td3()
    assert td3.validate("P<UTO").error is ErrorCode.FORMAT
    assert td3.validate(TD3.replace("C36", "C37")).error is ErrorCode.CHECKSUM
    assert td3.validate(TD3.replace("F1204", "Q1204")).error is ErrorCode.COMPONENT
    # Sex is not part of the composite: only the component rule catches the change.
    assert td3.validate(TD3.replace("UTO7408122F", "UTO7413122F")).error is ErrorCode.COMPONENT


@pytest.mark.parametrize("check", ["<", "0"])
def test_unknown_date_is_accepted_with_blank_or_zero_check_digit(check: str) -> None:
    l1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
    l2 = "L898902C36UTO" + "<<<<<<" + check + "F" + "120415" + "9" + "ZE184226B<<<<<" + "1"
    composite = check_digit(l2[0:10] + l2[13:20] + l2[21:43])
    mrz = f"{l1}{l2}{composite}"

    assert Td3().is_valid(mrz)
    data = Td3().parse(mrz)
    assert data is not None
    assert data.birth_date is None


def test_unknown_date_with_another_check_digit_is_a_component_error() -> None:
    l2 = "L898902C36UTO" + "<<<<<<" + "5" + "F" + "120415" + "9" + "ZE184226B<<<<<" + "1"
    mrz = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<" + l2 + "0"
    assert Td3().validate(mrz).error is ErrorCode.COMPONENT


def test_name_without_surname_is_a_component_error() -> None:
    mrz = TD3.replace("ERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<", "<" * 39)
    assert Td3().validate(mrz).error is ErrorCode.COMPONENT


def _long_td1(check: str) -> str:
    """TD1 MRZ with a 12-character number whose check digit is ``check``."""
    number = "ABC123456789"
    l1 = ("I<UTO" + number[:9] + "<" + number[9:] + check).ljust(30, "<")
    l2 = "7408122F1204159UTO" + "<" * 11
    composite = check_digit(l1[5:30] + l2[0:7] + l2[8:15] + l2[18:29])
    return f"{l1}{l2}{composite}" + "ERIKSSON<<ANNA".ljust(30, "<")


def test_document_number_longer_than_nine_characters_in_td1() -> None:
    mrz = _long_td1(str(check_digit("ABC123456789")))
    td1 = Td1()
    assert td1.is_valid(mrz)
    data = td1.parse(mrz)
    assert data is not None
    assert data.document_number == "ABC123456789"
    assert data.optional_data == ""  # the continuation is not repeated in the optional data

    # The composite covers the continuation: changing it is detected.
    assert not td1.is_valid(mrz[:16] + "0" + mrz[17:])


def test_long_number_check_digit_is_verified_even_if_composite_matches() -> None:
    wrong = str((check_digit("ABC123456789") + 1) % 10)
    assert Td1().validate(_long_td1(wrong)).error is ErrorCode.CHECKSUM


def test_nine_character_number_cannot_omit_its_check_digit() -> None:
    l1 = "I<UTOD23145890<<<<<<<<<<<<<<<<"
    l2 = "7408122F1204159UTO<<<<<<<<<<<"
    composite = check_digit(l1[5:30] + l2[0:7] + l2[8:15] + l2[18:29])
    mrz = f"{l1}{l2}{composite}" + "ERIKSSON<<ANNA".ljust(30, "<")
    assert Td1().validate(mrz).error is ErrorCode.CHECKSUM


def test_document_number_longer_than_nine_characters_in_td2() -> None:
    number = "ABC123456789"
    l1 = "I<UTOERIKSSON<<ANNA".ljust(36, "<")
    l2 = (
        "ABC123456" + "<" + "UTO" + "740812" + "2" + "F" + "120415" + "9"
        f"789{check_digit(number)}<<<"
    )
    composite = check_digit(l2[0:10] + l2[13:20] + l2[21:35])
    mrz = f"{l1}{l2}{composite}"

    assert Td2().is_valid(mrz)
    data = Td2().parse(mrz)
    assert data is not None
    assert data.document_number == number


def test_format_splits_lines() -> None:
    assert Td1().format(TD1.replace("\n", "")) == TD1
    assert Td2().format(TD2) == TD2
    assert Td3().format(TD3.replace("\n", "\r\n")) == TD3


def test_sex_x_and_unspecified() -> None:
    for sex in ("X", "<"):
        assert Td3().is_valid(TD3.replace("7408122F", f"7408122{sex}"))
    data = Td3().parse(TD3.replace("7408122F", "7408122<"))
    assert data is not None
    assert data.sex is None
