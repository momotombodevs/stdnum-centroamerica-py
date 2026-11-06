"""Guatemala documents: NIT and DPI (CUI)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from stdnum_centroamerica._base import BaseDocument, weighted_sum
from stdnum_centroamerica._random import rand_int, random_digits
from stdnum_centroamerica._types import ErrorCode

__all__ = ["Dpi", "DpiData", "Nit"]


class Nit(BaseDocument):
    """NIT (SAT). Level: complete (open-source formula).

    Modulo 11, check digit 0-9 or ``K``. Since 2023-10-04 new NITs are the first 9 digits of
    the CUI; with an 8-digit body both check digits agree (weights 9..2 and 2..9 add up to
    11), so no separate rule is needed.
    """

    __slots__ = ()

    _PATTERN = re.compile(r"[0-9]{1,11}[0-9K]", re.ASCII)

    def _check_content(self, prepared: str) -> ErrorCode | None:
        return None if self._check_digit(prepared[:-1]) == prepared[-1] else ErrorCode.CHECKSUM

    def generate(self) -> str:
        body = random_digits(rand_int(5, 8), non_zero_first=True)
        return body + self._check_digit(body)

    def format(self, number: str) -> str:
        return self._group_last(number)

    @staticmethod
    def _check_digit(body: str) -> str:
        """Check digit (``0``-``9`` or ``K``) of the NIT body."""
        total = weighted_sum(body, range(len(body) + 1, 1, -1))
        digit = (11 - total % 11) % 11
        return "K" if digit == 10 else str(digit)


@dataclass(frozen=True, slots=True)
class DpiData:
    """Components of a DPI. The registration number is left out of ``repr()``."""

    serial: str = field(repr=False)
    """The eight digits of the registration number."""

    department_code: int
    """Department of residence 1-22."""

    municipality_code: int
    """Municipality within the department."""


class Dpi(BaseDocument):
    """DPI / CUI (RENAP): 8 digits + check digit + department (2) + municipality (2).

    Level: complete for the check digit (weights 2..9, modulo 11; open-source formula) and the
    department (01-22). The municipality table of each department is not validated.
    """

    __slots__ = ()

    _PATTERN = re.compile(r"[0-9]{13}", re.ASCII)
    _DEPARTMENTS = 22

    def _check_content(self, prepared: str) -> ErrorCode | None:
        department = int(prepared[9:11])
        municipality = int(prepared[11:13])
        if not 1 <= department <= self._DEPARTMENTS or municipality < 1:
            return ErrorCode.COMPONENT
        return None if self._check_digit(prepared) == int(prepared[8]) else ErrorCode.CHECKSUM

    def generate(self) -> str:
        while True:
            body = random_digits(8)
            check = self._check_digit(body)
            if check != 10:
                break
        return f"{body}{check}{rand_int(1, self._DEPARTMENTS):02d}{rand_int(1, 20):02d}"

    def parse(self, number: str) -> DpiData | None:
        """Return the components of the number, or ``None`` if it is invalid."""
        compact = self._validated(number)
        if compact is None:
            return None
        return DpiData(
            serial=compact[:8],
            department_code=int(compact[9:11]),
            municipality_code=int(compact[11:13]),
        )

    def format(self, number: str) -> str:
        return self._group(number, (4, 5, 4), " ")

    @staticmethod
    def _check_digit(digits: str) -> int:
        """Check digit of the first 8 digits; 10 is not a digit and never appears in a CUI."""
        return weighted_sum(digits, range(2, 10)) % 11
