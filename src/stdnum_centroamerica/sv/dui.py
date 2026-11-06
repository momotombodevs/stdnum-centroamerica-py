"""El Salvador DUI."""

from __future__ import annotations

import re

from stdnum_centroamerica._base import BaseDocument, weighted_sum
from stdnum_centroamerica._random import random_digits
from stdnum_centroamerica._types import ErrorCode

__all__ = ["Dui"]


class Dui(BaseDocument):
    """DUI (RNPN): 8 digits + check digit, ``00000000-0``. Level: complete.

    Check digit: weights 9..2, modulo 10 (open-source formula; the RNPN does not publish it).
    """

    __slots__ = ()

    _PATTERN = re.compile(r"[0-9]{9}", re.ASCII)

    def _check_content(self, prepared: str) -> ErrorCode | None:
        return None if self._check_digit(prepared) == int(prepared[8]) else ErrorCode.CHECKSUM

    def generate(self) -> str:
        body = random_digits(8)
        return f"{body}{self._check_digit(body)}"

    def format(self, number: str) -> str:
        return self._group(number, (8, 1))

    @staticmethod
    def _check_digit(digits: str) -> int:
        """Check digit of the first 8 digits."""
        return (10 - weighted_sum(digits, range(9, 1, -1)) % 10) % 10
