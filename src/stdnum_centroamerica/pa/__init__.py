"""Panama documents: personal identity card (cédula) and RUC."""

from __future__ import annotations

import re
import string
from dataclasses import dataclass, field
from enum import StrEnum

from stdnum_centroamerica._base import DIGITS, BaseDocument, ensure_str
from stdnum_centroamerica._random import rand_int
from stdnum_centroamerica._types import ErrorCode

__all__ = ["Cedula", "CedulaData", "CedulaKind", "Ruc", "normalize"]

_PROVINCE = r"(?:1[0-3]|[1-9])"

# Characters stripped from both ends: space, \t, \n, \r, \0 and \v.
_TRIM = " \t\n\r\0\x0b"
# Group separators: ASCII whitespace and hyphens only (\s would accept Unicode spaces).
_SEPARATORS = re.compile(r"[ \t\n\r\f\v-]+", re.ASCII)
_UPPER = str.maketrans(string.ascii_lowercase, string.ascii_uppercase)


def _zero_groups(normalized: str) -> bool:
    """The groups that identify the person are all zeros: ``8-0-0``, ``8-NT-00-0``, ``E-8-0``.

    That is the volume and the entry, or the order number of a foreign resident (``E-P-ORDER``);
    the province does not identify anyone.
    """
    numbers = [group for group in normalized.split("-") if DIGITS.fullmatch(group)]
    identifying = numbers[-1:] if normalized.startswith("E-") else numbers[-2:]
    return len(numbers) >= 2 and all(group.strip("0") == "" for group in identifying)


def _canonical(number: str) -> str:
    """Normalized form without leading zeros per group: ``8-0926-01601`` is ``8-926-1601``."""
    return "-".join(
        group.lstrip("0") or "0" if DIGITS.fullmatch(group) else group
        for group in normalize(number).split("-")
    )


def normalize(number: str) -> str:
    """Upper-case, with a single hyphen between groups: the display form of cédula and RUC."""
    return _SEPARATORS.sub("-", ensure_str(number).strip(_TRIM)).translate(_UPPER)


class CedulaKind(StrEnum):
    """Kind of cédula, from its prefix."""

    BIRTH = "birth"
    """Born in Panama: ``P-VOLUME-ENTRY``."""

    BORN_ABROAD = "born_abroad"
    """Born abroad: ``PE-VOLUME-ENTRY``."""

    NATURALIZED = "naturalized"
    """Naturalized citizen: ``N-VOLUME-ENTRY``."""

    FOREIGN_RESIDENT = "foreign_resident"
    """Foreign resident: ``E-P-ORDER``."""


@dataclass(frozen=True, slots=True)
class CedulaData:
    """Components of a Panamanian cédula, as they appear in the number.

    Volume (tomo) and entry (asiento) are left out of ``repr()``: they identify the person.
    """

    kind: CedulaKind
    province_code: int | None = None
    """Province code (1-9 official; 10-13 from third-party sources); ``None`` for PE and N."""

    suffix: str | None = None
    """``PI`` (indigenous) or ``AV`` (predates the Civil Registry); third-party sources."""

    volume: str | None = field(default=None, repr=False)
    """Volume (tomo); ``None`` for a foreign resident."""

    entry: str = field(default="", repr=False)
    """Entry (asiento); for a foreign resident, the order number."""


class Cedula(BaseDocument):
    """Personal identity card (Electoral Tribunal). Level: format, no check digit.

    Volume and entry have variable length, so the hyphens are part of the number: the
    canonical form is :meth:`format` (:func:`normalize`); :meth:`compact`, as everywhere else
    in the package, strips the separators and therefore loses that information.

    Official forms (Decree 53 of 1958, art. 9, as quoted by the Electoral Tribunal):

    - birth: ``P-VOLUME-ENTRY`` (``8-926-1601``)
    - born abroad: ``PE-VOLUME-ENTRY`` (``PE-5-687``)
    - naturalized: ``N-VOLUME-ENTRY`` (``N-19-473``)
    - foreign resident: ``E-P-ORDER`` (``E-8-12345``)

    The province code P is 1-9 (provinces in alphabetical order). Unofficial (third-party
    sources): codes 10-13 (indigenous regions and Panamá Oeste) and the suffixes ``PI``
    (indigenous) and ``AV`` (predates the Civil Registry) between province and volume. Volume
    and entry lengths (1-6 digits) are permissive.
    """

    __slots__ = ()

    PATTERN = re.compile(
        rf"(?:{_PROVINCE}-(?:(?:PI|AV)-)?[0-9]{{1,6}}-[0-9]{{1,6}}"
        r"|PE-[0-9]{1,6}-[0-9]{1,6}"
        r"|N-[0-9]{1,6}-[0-9]{1,6}"
        rf"|E-{_PROVINCE}-[0-9]{{1,7}})",
        re.ASCII,
    )
    """Regex of the normalized form (use it with ``fullmatch``)."""

    _PATTERN = PATTERN

    def _prepare(self, number: str) -> str:
        return normalize(number)

    def generate(self) -> str:
        return f"{rand_int(1, 9)}-{rand_int(1, 999)}-{rand_int(1, 99999)}"

    def parse(self, number: str) -> CedulaData | None:
        """Return the components of the number, or ``None`` if it is invalid."""
        normalized = self._validated(number)
        if normalized is None:
            return None

        parts = normalized.split("-")
        match parts[0]:
            case "PE":
                return CedulaData(CedulaKind.BORN_ABROAD, volume=parts[1], entry=parts[2])
            case "N":
                return CedulaData(CedulaKind.NATURALIZED, volume=parts[1], entry=parts[2])
            case "E":
                return CedulaData(
                    CedulaKind.FOREIGN_RESIDENT, province_code=int(parts[1]), entry=parts[2]
                )
            case _ if len(parts) == 4:
                return CedulaData(CedulaKind.BIRTH, int(parts[0]), parts[1], parts[2], parts[3])
            case _:
                return CedulaData(CedulaKind.BIRTH, int(parts[0]), volume=parts[1], entry=parts[2])

    def format(self, number: str) -> str:
        return normalize(number)

    def _is_placeholder(self, prepared: str) -> bool:
        return _zero_groups(prepared)

    def canonical(self, number: str) -> str:
        """The normalized form without leading zeros per group (``8-0926-01601`` is
        ``8-926-1601``). It keeps the hyphens: :meth:`compact` merges different numbers."""
        return _canonical(number)


class Ruc(BaseDocument):
    """RUC (DGI). Level: format, without the check digits.

    The DGI e-invoice technical sheet defines the RUC as alphanumeric, 5 to 21 characters,
    with letters and hyphens. The 2-digit DV is assigned by the DGI system and its formula is
    not published, so it is not validated. As with :class:`Cedula`, the display form with
    hyphens is :meth:`format` and the form to store is :meth:`canonical`.

    A RUC like ``8-1-1`` matches both a natural person's cédula and the legal-entity form; the
    number alone does not say which.

    Accepted forms:

    - natural persons: the cédula.
    - foreigners with a PE cédula, as shown in the sheet: ``PE-P-VOLUME-ENTRY``
      (``PE-4-123-456``) and ``P-PE-VOLUME-ENTRY`` (``8-PE-3824-523``).
    - Tax Number (foreigners without a cédula): ``P-NT-VOLUME-ENTRY`` (``8-NT-123-45``).
    - legal entities: three numeric groups from the Public Registry
      (``00023824-0930-212623``). Permissive group lengths.
    """

    __slots__ = ()

    _OTHER_FORMS = (
        re.compile(
            rf"(?:PE-[0-9]{{1,6}}-[0-9]{{1,6}}-[0-9]{{1,6}}|{_PROVINCE}-PE-[0-9]{{1,6}}-[0-9]{{1,6}})",
            re.ASCII,
        ),
        re.compile(rf"{_PROVINCE}-NT-[0-9]{{1,6}}-[0-9]{{1,6}}", re.ASCII),
        re.compile(r"[0-9]{1,10}-[0-9]{1,6}-[0-9]{1,8}", re.ASCII),
    )

    def _prepare(self, number: str) -> str:
        return normalize(number)

    def _check(self, prepared: str) -> ErrorCode | None:
        if 5 <= len(prepared) <= 21 and any(
            pattern.fullmatch(prepared) is not None
            for pattern in (Cedula.PATTERN, *self._OTHER_FORMS)
        ):
            return None
        return ErrorCode.FORMAT

    def generate(self) -> str:
        """A cédula is a valid RUC (natural person)."""
        return Cedula().generate()

    def format(self, number: str) -> str:
        return normalize(number)

    def _is_placeholder(self, prepared: str) -> bool:
        return _zero_groups(prepared)

    def canonical(self, number: str) -> str:
        """The normalized form without leading zeros per group (``8-0926-01601`` is
        ``8-926-1601``). It keeps the hyphens: :meth:`compact` merges different numbers."""
        return _canonical(number)
