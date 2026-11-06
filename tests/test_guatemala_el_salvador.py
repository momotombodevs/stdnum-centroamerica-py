"""Guatemala and El Salvador: cases not covered by the shared vectors."""

from __future__ import annotations

from stdnum_centroamerica import ErrorCode
from stdnum_centroamerica.gt import Dpi, Nit
from stdnum_centroamerica.sv import Dui
from stdnum_centroamerica.sv import Nit as SvNit


def test_guatemala_nit_with_k_check_digit() -> None:
    # Find a synthetic body whose check digit is 10, i.e. K.
    body = next(
        f"{n:07d}" for n in range(1_000_000, 2_000_000) if Nit._check_digit(f"{n:07d}") == "K"
    )
    assert Nit().is_valid(body + "K")
    assert Nit().is_valid(body + "k")
    assert Nit().format(body + "k") == f"{body}-K"


def test_guatemala_nit_with_one_digit_body() -> None:
    assert Nit().validate("1").error is ErrorCode.FORMAT
    assert Nit().is_valid("1" + Nit._check_digit("1"))


def test_dpi_validates_department_and_municipality() -> None:
    assert Dpi().validate("1234567890001").error is ErrorCode.COMPONENT  # department 00
    assert Dpi().validate("1234567892301").error is ErrorCode.COMPONENT  # department 23
    assert Dpi().validate("1234567890100").error is ErrorCode.COMPONENT  # municipality 00
    assert Dpi().is_valid("1234567892201")


def test_dpi_format_with_spaces() -> None:
    assert Dpi().format("1234567890101") == "1234 56789 0101"
    assert Dpi().format("123") == "123"


def test_el_salvador_nit_delegates_9_digits_to_dui() -> None:
    assert SvNit().is_valid("12345678-4")
    assert SvNit().format("123456784") == "12345678-4"
    assert SvNit(dui=Dui()).validate("12345678-5").error is ErrorCode.CHECKSUM


def test_el_salvador_nit_with_letters_in_14_positions() -> None:
    assert SvNit().validate("0614130386136A").error is ErrorCode.FORMAT
