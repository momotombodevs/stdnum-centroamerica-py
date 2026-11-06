"""Nicaragua cédula and RUC."""

from __future__ import annotations

import string

import pytest

from stdnum_centroamerica import ErrorCode
from stdnum_centroamerica._data.nicaragua import KNOWN_CODES, MAX_CODE, MUNICIPALITY_CODES
from stdnum_centroamerica.ni import Cedula, Ruc


class TestCedula:
    def test_formats_and_compacts(self) -> None:
        doc = Cedula()
        assert doc.format("0010101900001N") == "001-010190-0001N"
        assert doc.compact("001-010190-0001n") == "0010101900001N"

    def test_letter_is_computed_modulo_23(self) -> None:
        assert Cedula.check_letter("0012510750012") == "S"

    @pytest.mark.parametrize("remainder", range(23))
    def test_every_letter_of_the_table(self, remainder: int) -> None:
        # Table from the open-source formula, typed here rather than imported: swapping two
        # letters in the package must fail. I, O, U and Z are not used.
        table = "ABCDEFGHJKLMNPQRSTUVWXY"
        base = 10101900000  # 001-010190-0000 without its leading zeros
        sequence = next(n for n in range(23) if (base + n) % 23 == remainder)
        digits = f"{base + sequence:013d}"
        assert Cedula.check_letter(digits) == table[remainder]
        assert Cedula(strict_letter=True).is_valid(digits + table[remainder])
        wrong = table[(remainder + 1) % 23]
        assert Cedula(strict_letter=True).validate(digits + wrong).error is ErrorCode.CHECKSUM

    @pytest.mark.parametrize("digits", ["", "12A", "١٢٣", "1_000", " 12"])
    def test_check_letter_requires_ascii_digits(self, digits: str) -> None:
        with pytest.raises(ValueError, match="ASCII digits"):
            Cedula.check_letter(digits)

    def test_strict_letter_mode(self) -> None:
        strict = Cedula(strict_letter=True)
        lenient = Cedula()
        assert strict.is_valid("001-251075-0012S")
        assert not strict.is_valid("001-251075-0012A")
        assert lenient.is_valid("001-251075-0012A")
        # Example from DGI notice AVISO/072/05-2022: it fails the modulo 23 check.
        assert not strict.is_valid("0013007660022M")
        assert lenient.is_valid("0013007660022M")

    def test_wrong_letter_is_accepted_by_default(self) -> None:
        assert Cedula().is_valid("001-010190-0001A")
        assert not Cedula().is_valid("001-010190-0001")
        assert Cedula(strict_letter=True).validate("001-010190-0001A").error is ErrorCode.CHECKSUM

    def test_strict_municipality_mode(self) -> None:
        # 282 is in the León block but is unassigned in the known list.
        number = "282-010190-0001" + Cedula.check_letter("2820101900001")
        assert Cedula().is_valid(number)
        assert not Cedula(strict_municipality=True).is_valid(number)
        assert Cedula(strict_municipality=True).is_valid("001-010190-0001N")

    def test_code_888_born_abroad(self) -> None:
        number = "888-010190-0001" + Cedula.check_letter("8880101900001")
        assert Cedula().is_valid(number)
        assert Cedula(strict_municipality=True).is_valid(number)
        assert not Cedula().is_valid("887-010190-0001" + Cedula.check_letter("8870101900001"))

    def test_sample_cedula_with_consistent_mrz(self) -> None:
        # Cédula infographic: 041 = Jinotepe, date 21-04-1994, production number 0000.
        assert Cedula.check_letter("0412104940000") == "Y"
        assert Cedula(strict_municipality=True).is_valid("041-210494-0000Y")

    def test_accepts_every_municipality_and_any_letter_by_default(self) -> None:
        doc = Cedula()
        ruc = Ruc()
        letters = string.ascii_uppercase
        assert MAX_CODE == 640  # 16 blocks of 40 codes; typed here, not imported
        for municipality in [*range(1, 641), 888]:
            number = (
                f"{municipality:03d}150690000{municipality % 10}"
                f"{letters[municipality % len(letters)]}"
            )
            assert doc.is_valid(number), number
            assert doc.is_valid(number.lower()), number
            assert ruc.is_valid(number), number

    def test_february_29_is_a_valid_date(self) -> None:
        assert Cedula().is_valid("001-290201-0001A")
        assert Cedula().validate("001-300201-0001A").error is ErrorCode.COMPONENT

    def test_municipality_table_has_no_duplicates(self) -> None:
        assert len(MUNICIPALITY_CODES) == len(KNOWN_CODES) == 152
        assert list(MUNICIPALITY_CODES) == sorted(MUNICIPALITY_CODES)
        assert all(1 <= code <= MAX_CODE for code in MUNICIPALITY_CODES)

    def test_options_are_keyword_only(self) -> None:
        with pytest.raises(TypeError):
            Cedula(True)  # type: ignore[call-arg]
        with pytest.raises(TypeError):
            Cedula(strictLetter=True)  # type: ignore[call-arg]

    def test_is_immutable(self) -> None:
        doc = Cedula()
        with pytest.raises(AttributeError, match="immutable"):
            doc._strict_letter = True
        with pytest.raises(AttributeError, match="immutable"):
            del doc._strict_letter


class TestRuc:
    def test_formats_and_compacts(self) -> None:
        doc = Ruc()
        assert doc.format("J0310000000001") == "J0310000000001"
        assert doc.compact("J0310000000001") == "J0310000000001"
        assert doc.format("0010101900001n") == "001-010190-0001N"

    def test_wrong_cedula_letter_only_fails_in_strict_mode(self) -> None:
        assert Ruc().is_valid("001-010190-0001A")
        assert not Ruc(cedula=Cedula(strict_letter=True)).is_valid("001-010190-0001A")

    def test_error_reasons(self) -> None:
        assert Ruc().validate("0000300766011M").error is ErrorCode.COMPONENT
        assert Ruc().validate("X").error is ErrorCode.FORMAT
        assert Ruc().validate("001-320190-0001N").error is ErrorCode.COMPONENT
