"""Machine readable zones (MRZ) from ICAO Doc 9303: TD1, TD2 and TD3.

Accepted with or without line breaks: lines have a fixed length, so :meth:`compact` joins
them. Level: complete (check digits).

Validates the format, the components (document code, sex, dates, characters of issuer,
nationality and name) and the check digits of the document number, birth date, expiry date,
optional data (TD3) and the composite. An unknown date (``<<<<<<``) takes ``<`` or ``0`` as
its check digit. Nothing is stored or logged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import ClassVar

from stdnum_centroamerica import _dates
from stdnum_centroamerica._base import BaseDocument
from stdnum_centroamerica._random import choice, rand_int, random_digits
from stdnum_centroamerica._types import ErrorCode

__all__ = ["MrzData", "Td1", "Td2", "Td3", "check_digit"]

_VALUES = {
    **{str(digit): digit for digit in range(10)},
    **{chr(ord("A") + i): 10 + i for i in range(26)},
    "<": 0,
}
_WEIGHTS = (7, 3, 1)

# No I or O, which are easily confused with 1 and 0.
_NUMBER_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789"
_SAMPLE_NAMES = {"ERIKSSON": "ANNA<MARIA", "SAMPLE": "JOHN", "EXAMPLE": "JANE<ROE"}
_UNKNOWN_DATE = "<<<<<<"

_CODE_SECOND = re.compile(r"[A-Z<]", re.ASCII)
_STATE = re.compile(r"[A-Z<]{3}", re.ASCII)
_NAME = re.compile(r"[A-Z][A-Z<]*", re.ASCII)
_DATE = re.compile(r"[0-9]{6}", re.ASCII)
_SEXES = frozenset({"M", "F", "X", "<"})


def check_digit(value: str) -> int:
    """Return the ICAO check digit (weights 7-3-1; ``A``=10 ... ``Z``=35; ``<``=0).

    :raises ValueError: if ``value`` has characters other than ``A-Z``, ``0-9`` and ``<``.
    """
    total = 0
    for i, char in enumerate(value):
        char_value = _VALUES.get(char)
        if char_value is None:
            message = "check_digit() only accepts A-Z, 0-9 and <"
            raise ValueError(message)
        total += char_value * _WEIGHTS[i % 3]
    return total % 10


@dataclass(frozen=True, slots=True)
class MrzData:
    """Data of a valid MRZ. Dates are YYMMDD as they appear: the century is not inferred.

    Names, document number, dates and optional data are left out of ``repr()``: they are
    personal data.
    """

    document_code: str
    """Document code, e.g. ``P`` (passport) or ``I`` (identity card)."""

    issuing_state: str
    """ICAO code of the issuing state, e.g. ``GTM``."""

    surname: str = field(repr=False)
    given_names: str = field(repr=False)
    document_number: str = field(repr=False)

    nationality: str
    """ICAO code of the nationality."""

    birth_date: str | None = field(repr=False)
    """YYMMDD, or ``None`` if unspecified."""

    sex: str | None
    """``M``, ``F`` or ``X``; ``None`` if unspecified."""

    expiry_date: str | None = field(repr=False)
    """YYMMDD, or ``None`` if unspecified."""

    optional_data: str = field(repr=False)
    """Personal number or other optional data, without filler."""


@dataclass(frozen=True, slots=True)
class _Fields:
    """Fields of a compact MRZ, already detached from the line layout."""

    code: str
    issuer: str
    name: str
    number: str
    """Full number, including the continuation when it exceeds nine characters."""
    number_check: str
    nationality: str
    birth: str
    birth_check: str
    sex: str
    expiry: str
    expiry_check: str
    optional: str
    """Optional data, without the number continuation or its check digit."""
    optional_check: str | None
    """Check digit of the optional data (TD3 only)."""
    composite_check: str
    composite_data: str
    """Text covered by the composite check digit, in specification order."""


def _pad(text: str, length: int) -> str:
    return text.ljust(length, "<")


def _matches(value: str, check: str) -> bool:
    return str(check_digit(value)) == check


def _optional_matches(value: str, check: str) -> bool:
    """With an empty field (all ``<``) the check digit may be ``<`` or ``0``."""
    if value.strip("<") == "":
        return check in ("<", "0")
    return _matches(value, check)


def _date_matches(date: str, check: str) -> bool:
    """An unknown date was already validated by :func:`_valid_date`."""
    return date == _UNKNOWN_DATE or _matches(date, check)


def _valid_date(date: str, check: str) -> bool:
    """A valid YYMMDD date, or an unknown one (``<<<<<<`` with check digit ``<`` or ``0``)."""
    if date == _UNKNOWN_DATE:
        return check in ("<", "0")
    return _DATE.fullmatch(date) is not None and _dates.is_valid_date(
        2000, int(date[2:4]), int(date[4:6])
    )


def _long_number(number: str, check: str, optional: str) -> tuple[str, str, str]:
    """Handle a document number longer than nine characters.

    Its check digit position holds ``<`` and the rest of the number plus its check digit go
    at the start of the optional data. Returns the full number, its check digit and the
    remaining optional data.
    """
    if check != "<":
        return number, check, optional
    head = optional.split("<", 1)[0]
    if head == "":
        return number, "<", optional
    return number + head[:-1], head[-1], optional[len(head) :]


def _random_holder() -> dict[str, str]:
    surname = choice(tuple(_SAMPLE_NAMES))
    return {
        "number": "".join(choice(_NUMBER_ALPHABET) for _ in range(9)),
        "birth": f"{rand_int(50, 99):02d}{rand_int(1, 12):02d}{rand_int(1, 28):02d}",
        "sex": choice("MF<"),
        "expiry": f"{rand_int(27, 40):02d}{rand_int(1, 12):02d}{rand_int(1, 28):02d}",
        "surname": surname,
        "given": _SAMPLE_NAMES[surname],
    }


class _BaseMrz(BaseDocument):
    __slots__ = ()

    _DOCUMENT_CODES: ClassVar[str] = ""
    """Allowed first letters of the document code."""

    _LINE_LENGTH: ClassVar[int] = 1
    _COMPOSITE_AT: ClassVar[int] = 0
    """Position (0-based) of the composite check digit in the compact MRZ."""

    def _fields(self, compact: str) -> _Fields:
        raise NotImplementedError

    def _draft(self) -> str:
        """Full MRZ with ``<`` in place of the composite check digit."""
        raise NotImplementedError

    @staticmethod
    def check_digit(value: str) -> int:
        """See :func:`stdnum_centroamerica.mrz.check_digit`."""
        return check_digit(value)

    def generate(self) -> str:
        draft = self._draft()
        composite = check_digit(self._fields(draft).composite_data)
        at = self._COMPOSITE_AT
        return f"{draft[:at]}{composite}{draft[at + 1 :]}"

    def parse(self, number: str) -> MrzData | None:
        """Return the MRZ data, or ``None`` if it is invalid.

        In TD1 both optional data fields are returned together.
        """
        compact = self._validated(number)
        if compact is None:
            return None

        fields = self._fields(compact)
        surname, _, given = fields.name.rstrip("<").partition("<<")
        return MrzData(
            document_code=fields.code.rstrip("<"),
            issuing_state=fields.issuer.rstrip("<"),
            surname=surname.replace("<", " ").strip(" "),
            given_names=given.replace("<", " ").strip(" "),
            document_number=fields.number.rstrip("<"),
            nationality=fields.nationality.rstrip("<"),
            birth_date=None if fields.birth == _UNKNOWN_DATE else fields.birth,
            sex=None if fields.sex == "<" else fields.sex,
            expiry_date=None if fields.expiry == _UNKNOWN_DATE else fields.expiry,
            optional_data=fields.optional.strip("<"),  # TD1: line 1 may be empty filler
        )

    def format(self, number: str) -> str:
        """Return each line on its own row."""
        compact = self.compact(number)
        size = self._LINE_LENGTH
        if len(compact) % size != 0:
            return compact
        return "\n".join(compact[i : i + size] for i in range(0, len(compact), size))

    def _check_content(self, prepared: str) -> ErrorCode | None:
        fields = self._fields(prepared)
        return self._check_components(fields) or self._check_digits(fields)

    def _is_placeholder(self, prepared: str) -> bool:
        return False  # names and codes are letters: zeros alone never make an empty MRZ

    def _check_components(self, f: _Fields) -> ErrorCode | None:
        valid = (
            f.code[0] in self._DOCUMENT_CODES
            and _CODE_SECOND.fullmatch(f.code[1]) is not None
            and _STATE.fullmatch(f.issuer) is not None
            and _STATE.fullmatch(f.nationality) is not None
            and _NAME.fullmatch(f.name) is not None
            and f.sex in _SEXES
            and _valid_date(f.birth, f.birth_check)
            and _valid_date(f.expiry, f.expiry_check)
        )
        return None if valid else ErrorCode.COMPONENT

    @staticmethod
    def _check_digits(f: _Fields) -> ErrorCode | None:
        valid = (
            _matches(f.number, f.number_check)
            and _date_matches(f.birth, f.birth_check)
            and _date_matches(f.expiry, f.expiry_check)
            and (f.optional_check is None or _optional_matches(f.optional, f.optional_check))
            and _matches(f.composite_data, f.composite_check)
        )
        return None if valid else ErrorCode.CHECKSUM


class Td1(_BaseMrz):
    """ID card MRZ (TD1): 3 lines of 30. ICAO Doc 9303, part 5.

    Line 1: code, issuer, number (6-14) and its check digit (15), optional data (16-30).
    Line 2: birth date and check digit, sex, expiry date and check digit, nationality,
    optional data (19-29) and the composite (30). Line 3: name.

    If the number exceeds nine characters, position 15 is ``<`` and the number continues in
    the optional data of line 1, followed by its check digit. Also accepts code ``P`` used by
    passport cards with this layout.
    """

    __slots__ = ()

    _PATTERN = re.compile(r"[A-Z0-9<]{90}", re.ASCII)
    _DOCUMENT_CODES = "ACIP"
    _LINE_LENGTH = 30
    _COMPOSITE_AT = 59

    def _fields(self, compact: str) -> _Fields:
        l1 = compact[0:30]
        l2 = compact[30:60]
        number, number_check, optional1 = _long_number(l1[5:14], l1[14], l1[15:30])
        return _Fields(
            code=l1[0:2],
            issuer=l1[2:5],
            name=compact[60:90],
            number=number,
            number_check=number_check,
            nationality=l2[15:18],
            birth=l2[0:6],
            birth_check=l2[6],
            sex=l2[7],
            expiry=l2[8:14],
            expiry_check=l2[14],
            optional=optional1 + l2[18:29],
            optional_check=None,
            composite_check=l2[29],
            composite_data=l1[5:30] + l2[0:7] + l2[8:15] + l2[18:29],
        )

    def _draft(self) -> str:
        h = _random_holder()
        return (
            f"I<UTO{h['number']}{check_digit(h['number'])}{_pad('', 15)}"
            f"{h['birth']}{check_digit(h['birth'])}{h['sex']}"
            f"{h['expiry']}{check_digit(h['expiry'])}UTO{_pad('', 11)}<"
            f"{_pad(h['surname'] + '<<' + h['given'], 30)}"
        )


class Td2(_BaseMrz):
    """ID document MRZ (TD2): 2 lines of 36. ICAO Doc 9303, part 6.

    Line 2: number (1-9) and check digit, nationality, birth date and check digit, sex,
    expiry date and check digit, optional data (29-35) and the composite (36). If the number
    exceeds nine characters, position 10 is ``<`` and the number continues in the optional
    data, followed by its check digit.
    """

    __slots__ = ()

    _PATTERN = re.compile(r"[A-Z0-9<]{72}", re.ASCII)
    _DOCUMENT_CODES = "ACI"
    _LINE_LENGTH = 36
    _COMPOSITE_AT = 71

    def _fields(self, compact: str) -> _Fields:
        l1 = compact[0:36]
        l2 = compact[36:72]
        number, number_check, optional = _long_number(l2[0:9], l2[9], l2[28:35])
        return _Fields(
            code=l1[0:2],
            issuer=l1[2:5],
            name=l1[5:],
            number=number,
            number_check=number_check,
            nationality=l2[10:13],
            birth=l2[13:19],
            birth_check=l2[19],
            sex=l2[20],
            expiry=l2[21:27],
            expiry_check=l2[27],
            optional=optional,
            optional_check=None,
            composite_check=l2[35],
            composite_data=l2[0:10] + l2[13:20] + l2[21:35],
        )

    def _draft(self) -> str:
        h = _random_holder()
        return (
            f"{_pad('I<UTO' + h['surname'] + '<<' + h['given'], 36)}"
            f"{h['number']}{check_digit(h['number'])}UTO"
            f"{h['birth']}{check_digit(h['birth'])}{h['sex']}"
            f"{h['expiry']}{check_digit(h['expiry'])}{_pad('', 7)}<"
        )


class Td3(_BaseMrz):
    """Passport MRZ (TD3): 2 lines of 44. ICAO Doc 9303, part 4.

    Line 2: number (1-9) and check digit, nationality, birth date and check digit, sex,
    expiry date and check digit, optional data (29-42) with its check digit (43) and the
    composite (44).
    """

    __slots__ = ()

    _PATTERN = re.compile(r"[A-Z0-9<]{88}", re.ASCII)
    _DOCUMENT_CODES = "P"
    _LINE_LENGTH = 44
    _COMPOSITE_AT = 87

    def _fields(self, compact: str) -> _Fields:
        l1 = compact[0:44]
        l2 = compact[44:88]
        return _Fields(
            code=l1[0:2],
            issuer=l1[2:5],
            name=l1[5:],
            number=l2[0:9],
            number_check=l2[9],
            nationality=l2[10:13],
            birth=l2[13:19],
            birth_check=l2[19],
            sex=l2[20],
            expiry=l2[21:27],
            expiry_check=l2[27],
            optional=l2[28:42],
            optional_check=l2[42],
            composite_check=l2[43],
            composite_data=l2[0:10] + l2[13:20] + l2[21:43],
        )

    def _draft(self) -> str:
        h = _random_holder()
        optional = _pad(random_digits(9) if rand_int(0, 1) == 1 else "", 14)
        optional_check = "<" if optional.strip("<") == "" else str(check_digit(optional))
        return (
            f"{_pad('P<UTO' + h['surname'] + '<<' + h['given'], 44)}"
            f"{h['number']}{check_digit(h['number'])}UTO"
            f"{h['birth']}{check_digit(h['birth'])}{h['sex']}"
            f"{h['expiry']}{check_digit(h['expiry'])}"
            f"{optional}{optional_check}<"
        )
