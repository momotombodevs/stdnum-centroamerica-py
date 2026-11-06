"""Base class for documents and shared helpers."""

from __future__ import annotations

import re
import string
from collections.abc import Iterable, Mapping
from typing import Any, ClassVar, NoReturn

from stdnum_centroamerica._types import ErrorCode, ValidationResult

__all__ = ["DIGITS", "MAX_INPUT_LENGTH", "BaseDocument", "ensure_str", "weighted_sum"]

MAX_INPUT_LENGTH = 256
"""Maximum accepted input length. A TD1 MRZ (90 characters plus line breaks) fits easily.
Longer inputs are rejected as ``FORMAT`` without running any regular expression."""

DIGITS = re.compile(r"[0-9]+", re.ASCII)
"""One or more ASCII digits. ``str.isdigit()`` is not enough: it accepts non-ASCII digits."""

# Strips ASCII whitespace and hyphens and upper-cases ASCII letters only: str.upper() turns
# "ß" into "SS" and the Turkish dotless i into "I", which could make invalid input valid.
_COMPACT_TABLE = str.maketrans(string.ascii_lowercase, string.ascii_uppercase, " \t\n\r\f\v-")

_RESULTS: Mapping[ErrorCode | None, ValidationResult] = {
    None: ValidationResult(),
    **{code: ValidationResult(code) for code in ErrorCode},
}


def ensure_str(value: object) -> str:
    """Return ``value`` if it is a ``str``; otherwise raise ``TypeError`` without echoing it."""
    if not isinstance(value, str):
        _raise_type_error(value)
    return value


def _raise_type_error(value: object) -> NoReturn:
    message = f"expected str, got {type(value).__name__}"
    raise TypeError(message)


def _rebuild(cls: type[BaseDocument], options: dict[str, Any]) -> BaseDocument:
    return cls(**options)


def _all_zero(prepared: str) -> bool:
    """Return ``True`` if the number has digits and every one of them is ``0``."""
    digits = [char for char in prepared if char in string.digits]
    return bool(digits) and all(char == "0" for char in digits)


def weighted_sum(digits: str, weights: Iterable[int]) -> int:
    """Sum of each digit times its weight, left to right (one weight per digit)."""
    return sum(int(digits[i]) * weight for i, weight in enumerate(weights))


class BaseDocument:
    """Base class of the bundled documents.

    Subclasses define ``_PATTERN`` (the regex the prepared form must fully match) and, when
    needed, ``_check_content()`` with additional rules. Documents that cannot be expressed
    with a single pattern override ``_check()``. ``_prepare()`` changes the form that is
    validated (the compact form by default; Panama keeps the hyphens).

    Instances are immutable, so they can be shared across threads.
    """

    __slots__ = ()

    _PATTERN: ClassVar[re.Pattern[str] | None] = None

    def __setattr__(self, name: str, value: object) -> NoReturn:
        message = f"{type(self).__name__} is immutable"
        raise AttributeError(message)

    def __delattr__(self, name: str) -> NoReturn:
        message = f"{type(self).__name__} is immutable"
        raise AttributeError(message)

    def _init_attr(self, name: str, value: object) -> None:
        """Set an attribute from ``__init__``, bypassing the immutability guard."""
        object.__setattr__(self, name, value)

    def _options(self) -> Mapping[str, Any]:
        """Constructor options, used by ``repr()``, equality and pickling."""
        return {}

    def __repr__(self) -> str:
        options = ", ".join(f"{name}={value!r}" for name, value in self._options().items())
        return f"{type(self).__name__}({options})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseDocument) or type(other) is not type(self):
            return NotImplemented
        return dict(self._options()) == dict(other._options())

    def __hash__(self) -> int:
        return hash((type(self), tuple(sorted(self._options().items()))))

    def __reduce__(self) -> tuple[Any, ...]:
        # pickle and copy.deepcopy rebuild through the constructor, not through __setattr__.
        return (_rebuild, (type(self), dict(self._options())))

    # -- public API --------------------------------------------------------------------

    def is_valid(self, number: str) -> bool:
        """Return ``True`` if the number is valid."""
        return self._error(number) is None

    def validate(self, number: str) -> ValidationResult:
        """Return the result, with the failure reason (``ErrorCode``) if the number is invalid."""
        return _RESULTS[self._error(number)]

    def compact(self, number: str) -> str:
        """Return the number without whitespace or hyphens, upper-cased."""
        return ensure_str(number).translate(_COMPACT_TABLE)

    def format(self, number: str) -> str:
        """Return the display form. Without a grouping of its own, it is the compact form."""
        return self.compact(number)

    def canonical(self, number: str) -> str:
        """Return the form to store: the compact form, unless it loses information.

        Two different valid numbers never share a canonical form, and variants of the same
        number do. Panama overrides it, because its hyphens are part of the number; documents
        whose leading zeros carry no meaning (``gt.nit``, ``sv.nrc``) drop them.
        """
        return self.compact(number)

    # -- validation --------------------------------------------------------------------

    def _error(self, number: str) -> ErrorCode | None:
        number = ensure_str(number)
        if len(number) > MAX_INPUT_LENGTH or not number.isascii():
            return ErrorCode.FORMAT
        prepared = self._prepare(number)
        error = self._check(prepared)
        if error is None and self._is_placeholder(prepared):
            return ErrorCode.COMPONENT
        return error

    def _validated(self, number: str) -> str | None:
        """Return the validated form of the number, or ``None``: the basis of ``parse()``."""
        if self._error(number) is not None:
            return None
        return self._prepare(number)

    def _prepare(self, number: str) -> str:
        return self.compact(number)

    def _check(self, prepared: str) -> ErrorCode | None:
        pattern = self._PATTERN
        if pattern is None:
            raise NotImplementedError
        if pattern.fullmatch(prepared) is None:
            return ErrorCode.FORMAT
        return self._check_content(prepared)

    def _check_content(self, prepared: str) -> ErrorCode | None:
        """Additional rules for a number that already matches ``_PATTERN``."""
        return None

    def _is_placeholder(self, prepared: str) -> bool:
        """``True`` for a valid-looking placeholder: every digit is zero (``00000000-0``)."""
        return _all_zero(prepared)

    # -- formatting --------------------------------------------------------------------

    def _group(self, number: str, sizes: Iterable[int], separator: str = "-") -> str:
        """Group the compact number; if the length does not match, return it compact."""
        compact = self.compact(number)
        sizes = tuple(sizes)
        if len(compact) != sum(sizes):
            return compact
        parts = []
        offset = 0
        for size in sizes:
            parts.append(compact[offset : offset + size])
            offset += size
        return separator.join(parts)

    def _group_last(self, number: str) -> str:
        """Separate the last character (the check digit) from the rest with a hyphen."""
        compact = self.compact(number)
        if len(compact) < 2:
            return compact
        return f"{compact[:-1]}-{compact[-1]}"
