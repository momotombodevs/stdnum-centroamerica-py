"""El Salvador NRC."""

from __future__ import annotations

import re

from stdnum_centroamerica._base import BaseDocument
from stdnum_centroamerica._random import rand_int, random_digits

__all__ = ["Nrc"]


class Nrc(BaseDocument):
    """NRC (Ministry of Finance): 1 to 8 digits. Level: format.

    As defined by the DTE schemas (``^[0-9]{1,8}$``; the consumer invoice requires at
    least 2).
    """

    __slots__ = ()

    _PATTERN = re.compile(r"[0-9]{1,8}", re.ASCII)

    def format(self, number: str) -> str:
        return self._group_last(number)

    def generate(self) -> str:
        return random_digits(rand_int(1, 8))
