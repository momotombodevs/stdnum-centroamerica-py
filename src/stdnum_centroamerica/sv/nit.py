"""El Salvador NIT."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from stdnum_centroamerica._base import DIGITS, BaseDocument, weighted_sum
from stdnum_centroamerica._random import random_digits
from stdnum_centroamerica._types import ErrorCode
from stdnum_centroamerica.sv.dui import Dui

__all__ = ["Nit"]

_LEGACY_WEIGHTS = tuple((2, 7, 6, 5, 4, 3)[i % 6] for i in range(13))


class Nit(BaseDocument):
    """NIT (Ministry of Finance), ``0000-000000-000-0``. Level: complete.

    The DTE schemas accept 14 digits or 9 (the DUI, which serves as the NIT of natural
    persons); a 9-digit number is validated as a DUI.

    14-digit check digit (formula from the open-source library idsv-php; the Ministry does
    not publish it): if the sequence number (positions 11-13) is <= 100, weights 14..2 and
    the remainder modulo 11 (10 becomes 0); otherwise, weights 2,7,6,5,4,3 repeated and the
    digit is 11 - remainder (0 if the remainder is 0 or 1). The three sample NITs in the
    official DTE integration guide satisfy it.
    """

    __slots__ = ("_dui",)

    _dui: Dui

    def __init__(self, *, dui: Dui | None = None) -> None:
        self._init_attr("_dui", dui if dui is not None else Dui())

    def _options(self) -> Mapping[str, Any]:
        return {"dui": self._dui}

    def _check(self, prepared: str) -> ErrorCode | None:
        if len(prepared) == 9:
            return self._dui.validate(prepared).error
        if len(prepared) != 14 or DIGITS.fullmatch(prepared) is None:
            return ErrorCode.FORMAT
        return None if self._check_digit(prepared) == int(prepared[13]) else ErrorCode.CHECKSUM

    def generate(self) -> str:
        body = random_digits(13)
        return f"{body}{self._check_digit(body + '0')}"

    def format(self, number: str) -> str:
        if len(self.compact(number)) == 9:
            return self._dui.format(number)
        return self._group(number, (4, 6, 3, 1))

    @staticmethod
    def _check_digit(nit: str) -> int:
        """Check digit of a 14-digit NIT (the last digit is ignored)."""
        if int(nit[10:13]) <= 100:
            remainder = weighted_sum(nit, range(14, 1, -1)) % 11
            return 0 if remainder == 10 else remainder
        remainder = weighted_sum(nit, _LEGACY_WEIGHTS) % 11
        return 11 - remainder if remainder > 1 else 0
