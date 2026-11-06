"""Randomness for ``generate()``.

Uses :mod:`secrets` even though the numbers are synthetic and meant for tests: it costs the
same as :mod:`random` and keeps security scanners quiet.
"""

from __future__ import annotations

import secrets
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


def rand_int(low: int, high: int) -> int:
    """Return a random integer between ``low`` and ``high``, both inclusive."""
    return low + secrets.randbelow(high - low + 1)


def choice(items: Sequence[T]) -> T:
    """Return a random element of a non-empty sequence."""
    return secrets.choice(items)


def random_digits(length: int, *, non_zero_first: bool = False) -> str:
    """Return ``length`` random digits, never all zeros; ``non_zero_first`` avoids a leading zero.

    All zeros is rejected by validation, so it is never generated.
    """
    if length < 1:
        return ""
    while True:
        digits = "".join(
            str(rand_int(1 if i == 0 and non_zero_first else 0, 9)) for i in range(length)
        )
        if digits.strip("0"):
            return digits
