"""Costa Rica documents: cédula física, cédula jurídica, DIMEX and NITE.

Rules from the Ministry of Finance (Hacienda), annexes and structures v4.4. All of them are
format-level (no check digit).
"""

from __future__ import annotations

import re

from stdnum_centroamerica._base import BaseDocument
from stdnum_centroamerica._random import rand_int, random_digits

__all__ = ["CedulaFisica", "CedulaJuridica", "Dimex", "Nite"]


class CedulaFisica(BaseDocument):
    """Identity card (TSE): 9 digits without a leading zero, ``0-0000-0000``."""

    __slots__ = ()

    _PATTERN = re.compile(r"[1-9][0-9]{8}", re.ASCII)

    def format(self, number: str) -> str:
        return self._group(number, (1, 4, 4))

    def generate(self) -> str:
        return random_digits(9, non_zero_first=True)


class CedulaJuridica(BaseDocument):
    """Legal entity number: 10 digits, ``0-000-000000``."""

    __slots__ = ()

    _PATTERN = re.compile(r"[0-9]{10}", re.ASCII)

    def format(self, number: str) -> str:
        return self._group(number, (1, 3, 6))

    def generate(self) -> str:
        return random_digits(10)


class Dimex(BaseDocument):
    """DIMEX (immigration): 11 or 12 digits without a leading zero."""

    __slots__ = ()

    _PATTERN = re.compile(r"[1-9][0-9]{10,11}", re.ASCII)

    def generate(self) -> str:
        return random_digits(rand_int(11, 12), non_zero_first=True)


class Nite(BaseDocument):
    """NITE (tax administration): 10 digits."""

    __slots__ = ()

    _PATTERN = re.compile(r"[0-9]{10}", re.ASCII)

    def generate(self) -> str:
        return random_digits(10)
