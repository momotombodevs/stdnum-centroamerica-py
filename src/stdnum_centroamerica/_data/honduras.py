"""Administrative divisions of Honduras: 18 departments, 298 municipalities.

The 4-digit code is department (2) + municipality (2, sequential 01..n).

Counts checked on 2026-10-19 against the INE (2013 census, municipal volumes): the
"División política y códigos municipales" lists of each department and the numbering of the
298 volumes (e.g. Villeda Morales 09-06, San Francisco de Opalaca 10-17).
Legal basis of the code: RNP Law (Decree 62-2004), arts. 99-100.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

MUNICIPALITIES_BY_DEPARTMENT: Mapping[int, int] = MappingProxyType(
    {
        1: 8,  # Atlántida
        2: 10,  # Colón
        3: 21,  # Comayagua
        4: 23,  # Copán
        5: 12,  # Cortés
        6: 16,  # Choluteca
        7: 19,  # El Paraíso
        8: 28,  # Francisco Morazán
        9: 6,  # Gracias a Dios
        10: 17,  # Intibucá
        11: 4,  # Islas de la Bahía
        12: 19,  # La Paz
        13: 28,  # Lempira
        14: 16,  # Ocotepeque
        15: 23,  # Olancho
        16: 28,  # Santa Bárbara
        17: 9,  # Valle
        18: 11,  # Yoro
    }
)
"""Department => number of municipalities."""

SPECIAL_CODES: frozenset[str] = frozenset({"0880", "0890"})
"""Official special codes (RNP Law Regulation, Agreement 73): 0880 dual nationality
(art. 153) and 0890 naturalized citizens (art. 150). The RNP may create others "in duly
justified cases" (Law, art. 100)."""
