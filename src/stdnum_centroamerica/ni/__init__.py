"""Nicaragua documents: identity card (cédula) and RUC."""

from __future__ import annotations

import datetime
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from stdnum_centroamerica import _dates
from stdnum_centroamerica._base import DIGITS, BaseDocument
from stdnum_centroamerica._data.nicaragua import (
    FOREIGN_CODE,
    KNOWN_CODES,
    MAX_CODE,
    MUNICIPALITY_CODES,
)
from stdnum_centroamerica._random import choice, rand_int, random_digits
from stdnum_centroamerica._types import ErrorCode

__all__ = ["Cedula", "CedulaData", "Ruc"]

_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXY"
_CEDULA = re.compile(r"([0-9]{3})([0-9]{2})([0-9]{2})[0-9]{6}([A-Z])", re.ASCII)


@dataclass(frozen=True, slots=True)
class CedulaData:
    """Components of a Nicaraguan cédula.

    The municipality and the letter are not checked against the CSE: the code list and the
    letter formula come from third parties (see ``docs/sources.md``). The birth date and the
    sequence number are left out of ``repr()``: they are personal data.
    """

    municipality_code: int
    """Municipality code; 888 means born abroad (single source)."""

    birth_day: int = field(repr=False)
    birth_month: int = field(repr=False)
    birth_year_two_digits: int = field(repr=False)
    """Two-digit birth year; the century is not part of the number."""

    sequence: str = field(repr=False)
    """Four-digit sequence number."""

    letter: str
    """Check letter as it appears in the number."""

    def is_born_abroad(self) -> bool:
        """Code 888: the number does not identify a municipality."""
        return self.municipality_code == FOREIGN_CODE

    def birth_year_candidates(self, today: datetime.date | None = None) -> tuple[int, ...]:
        """Return the possible birth years: 19YY or 20YY.

        Drops the years that would put the birth date after ``today`` (default: today) and
        those without that day (February 29 in a non-leap year). It may be empty: 29/02/01
        exists neither in 1901 nor in 2001.

        Do not use it to decide whether someone is of age: a person born in 2010 also gets
        the candidate 1910.
        """
        reference = today if today is not None else _dates.today()
        limit = (reference.year, reference.month, reference.day)
        return tuple(
            year
            for year in (1900 + self.birth_year_two_digits, 2000 + self.birth_year_two_digits)
            if _dates.is_valid_date(year, self.birth_month, self.birth_day)
            and (year, self.birth_month, self.birth_day) <= limit
        )


class Cedula(BaseDocument):
    """Identity card (CSE), ``000-000000-0000A``. Level: format (complete with ``strict_letter``).

    Municipality (3) + birth date DDMMYY (6) + sequence number (4) + letter. Law 152, art. 31,
    defines the 13 digits; it does not mention the letter.

    Validates the format, a plausible date and a municipality in 001-640 (or 888, born
    abroad). The letter is computed from the 13 digits modulo 23 over
    ``ABCDEFGHJKLMNPQRSTUVWXY``, from open sources; the CSE does not publish the formula, so
    by default the last character only has to be a letter.

    Options:

    - ``strict_letter=True`` checks the letter.
    - ``strict_municipality=True`` requires a code from the known list, which is incomplete,
      so it may reject valid cédulas.
    """

    __slots__ = ("_strict_letter", "_strict_municipality")

    _strict_letter: bool
    _strict_municipality: bool

    def __init__(self, *, strict_municipality: bool = False, strict_letter: bool = False) -> None:
        self._init_attr("_strict_municipality", bool(strict_municipality))
        self._init_attr("_strict_letter", bool(strict_letter))

    def _options(self) -> Mapping[str, Any]:
        return {
            "strict_municipality": self._strict_municipality,
            "strict_letter": self._strict_letter,
        }

    def _check(self, prepared: str) -> ErrorCode | None:
        match = _CEDULA.fullmatch(prepared)
        if match is None:
            return ErrorCode.FORMAT

        municipality, day, month, letter = match.groups()
        if not self._is_known_municipality(int(municipality)) or not _dates.is_valid_date(
            2000, int(month), int(day)
        ):
            return ErrorCode.COMPONENT

        if self._strict_letter and self.check_letter(prepared[:13]) != letter:
            return ErrorCode.CHECKSUM
        return None

    def generate(self) -> str:
        municipality = choice(MUNICIPALITY_CODES)
        digits = (
            f"{municipality:03d}{rand_int(1, 28):02d}{rand_int(1, 12):02d}{rand_int(0, 99):02d}"
            f"{random_digits(4)}"
        )
        return digits + self.check_letter(digits)

    def parse(self, number: str) -> CedulaData | None:
        """Return the components of the number, or ``None`` if it is invalid."""
        compact = self._validated(number)
        if compact is None:
            return None
        return CedulaData(
            municipality_code=int(compact[0:3]),
            birth_day=int(compact[3:5]),
            birth_month=int(compact[5:7]),
            birth_year_two_digits=int(compact[7:9]),
            sequence=compact[9:13],
            letter=compact[13],
        )

    def format(self, number: str) -> str:
        return self._group(number, (3, 6, 5))

    @staticmethod
    def check_letter(digits: str) -> str:
        """Return the check letter (modulo 23) of the 13 digits of a cédula.

        :raises ValueError: if ``digits`` contains anything other than ASCII digits.
        """
        if not isinstance(digits, str) or DIGITS.fullmatch(digits) is None:
            message = "check_letter() expects ASCII digits only"
            raise ValueError(message)
        return _LETTERS[int(digits) % 23]

    def _is_known_municipality(self, code: int) -> bool:
        if code == FOREIGN_CODE:
            return True
        return 1 <= code <= MAX_CODE and (not self._strict_municipality or code in KNOWN_CODES)


class Ruc(BaseDocument):
    """RUC (DGI), 14 characters. Level: format.

    Legal entities: ``J`` + 13 digits; nationals without a cédula ``N``, foreign residents
    ``R`` and non-residents ``E`` (+ 13 digits); nationals with a cédula use their cédula
    number. Numbers starting with four zeros are invalid.
    Source: DGI, AVISO/072/05-2022 (General Administrative Provision 01-2013).

    ``cedula`` is the :class:`Cedula` used to validate the RUC of natural persons, e.g.
    ``Ruc(cedula=Cedula(strict_letter=True))``.
    """

    __slots__ = ("_cedula",)

    _cedula: Cedula

    _PREFIXED = re.compile(r"[JNRE][0-9]{13}", re.ASCII)
    _PREFIXES = ("J", "N", "R", "E")

    def __init__(self, *, cedula: Cedula | None = None) -> None:
        self._init_attr("_cedula", cedula if cedula is not None else Cedula())

    def _options(self) -> Mapping[str, Any]:
        return {"cedula": self._cedula}

    def _check(self, prepared: str) -> ErrorCode | None:
        if prepared.startswith("0000"):
            return ErrorCode.COMPONENT
        if self._PREFIXED.fullmatch(prepared) is not None:
            return None
        return self._cedula.validate(prepared).error

    def generate(self) -> str:
        return choice(self._PREFIXES) + random_digits(13)

    def format(self, number: str) -> str:
        compact = self.compact(number)
        if compact[:1] in self._PREFIXES:
            return compact
        return self._cedula.format(compact)
