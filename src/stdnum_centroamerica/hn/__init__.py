"""Honduras documents: identity number and RTN."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from stdnum_centroamerica import _dates
from stdnum_centroamerica._base import BaseDocument
from stdnum_centroamerica._data.honduras import MUNICIPALITIES_BY_DEPARTMENT, SPECIAL_CODES
from stdnum_centroamerica._random import rand_int, random_digits
from stdnum_centroamerica._types import ErrorCode

__all__ = ["Identidad", "IdentidadData", "Rtn"]


@dataclass(frozen=True, slots=True)
class IdentidadData:
    """Components of a Honduran identity number.

    The registration year and the sequence number are left out of ``repr()``: they are
    personal data.
    """

    department_code: int | None
    """Department 1-18; ``None`` for a special code."""

    municipality_code: int | None
    """Municipality within the department; ``None`` for a special code."""

    registration_year: int = field(repr=False)
    """Registration year (for naturalized citizens, the year of the naturalization decree)."""

    sequence: str = field(repr=False)
    """Five-digit sequence number."""

    special_code: str | None
    """``"0880"`` (dual nationality) or ``"0890"`` (naturalized citizens)."""


class Identidad(BaseDocument):
    """Identity number (RNP): 13 digits, ``0000-0000-00000``. Level: format + geography.

    Department (2) + municipality (2) + registration year (4) + sequence number (5).

    Validates department 01-18, a municipality within the department's actual count and a
    registration year that is not in the future. Accepts the official special codes 0880
    (dual nationality) and 0890 (naturalized citizens; the year is that of the decree).
    There is no check digit.
    """

    __slots__ = ()

    _PATTERN = re.compile(r"[0-9]{13}", re.ASCII)

    def _check_content(self, prepared: str) -> ErrorCode | None:
        year = int(prepared[4:8])
        if year < 1800 or year > _dates.today().year:
            return ErrorCode.COMPONENT

        code = prepared[:4]
        if code in SPECIAL_CODES:
            return None

        municipalities = MUNICIPALITIES_BY_DEPARTMENT.get(int(code[:2]), 0)
        municipality = int(code[2:4])
        return None if 1 <= municipality <= municipalities else ErrorCode.COMPONENT

    def generate(self) -> str:
        department = rand_int(1, 18)
        municipality = rand_int(1, MUNICIPALITIES_BY_DEPARTMENT[department])
        return f"{department:02d}{municipality:02d}{rand_int(1950, 2005):04d}{random_digits(5)}"

    def parse(self, number: str) -> IdentidadData | None:
        """Return the components of the number, or ``None`` if it is invalid."""
        compact = self._validated(number)
        if compact is None:
            return None

        code = compact[:4]
        special = code in SPECIAL_CODES
        return IdentidadData(
            department_code=None if special else int(code[:2]),
            municipality_code=None if special else int(code[2:4]),
            registration_year=int(compact[4:8]),
            sequence=compact[8:13],
            special_code=code if special else None,
        )

    def format(self, number: str) -> str:
        return self._group(number, (4, 4, 5))


class Rtn(BaseDocument):
    """RTN (SAR): 14 digits; for natural persons, the identity number + 1 digit. Level: format."""

    __slots__ = ()

    _PATTERN = re.compile(r"[0-9]{14}", re.ASCII)

    def generate(self) -> str:
        return random_digits(14)
