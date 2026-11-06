"""Municipality codes of the Nicaraguan cédula (first 3 digits).

Source: third-party list (gist "Validacion Cedula Nicaraguense", reproduced by
bnorvinjosue/cedula-nicaragua-validator); the CSE does not publish the table. Checked on
2026-10-19. Against the official INIDE table (153 municipalities), 149 of the 152 codes fall
in the right department. Exceptions and gaps:

- Mulukukú (North Caribbean Coast, created in 2005) is missing;
- 492 appears as Wiwilí in the Nueva Segovia block; it is Wiwilí de Jinotega;
- 454 Waslala is in the Matagalpa block but belongs to the North Caribbean Coast;
- the 40-code blocks have unused gaps (e.g. 282 in León).
"""

from __future__ import annotations

MUNICIPALITY_CODES: tuple[int, ...] = (
    1, 2, 3, 4, 5, 6, 7, 8, 9, 41, 42, 43,
    44, 45, 46, 47, 48, 81, 82, 83, 84, 85, 86, 87,
    88, 89, 90, 91, 92, 93, 121, 122, 123, 124, 125, 126,
    127, 128, 129, 130, 161, 162, 163, 164, 165, 166, 201, 202,
    203, 204, 241, 242, 243, 244, 245, 246, 247, 281, 283, 284,
    285, 286, 287, 288, 289, 290, 291, 321, 322, 323, 324, 325,
    326, 327, 328, 329, 361, 362, 363, 364, 365, 366, 401, 402,
    403, 404, 405, 406, 407, 408, 409, 441, 442, 443, 444, 445,
    446, 447, 448, 449, 450, 451, 452, 453, 454, 481, 482, 483,
    484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 521, 522,
    523, 524, 525, 526, 561, 562, 563, 564, 565, 566, 567, 568,
    569, 570, 601, 602, 603, 604, 605, 606, 607, 608, 610, 611,
    612, 615, 616, 619, 624, 626, 627, 628,
)  # fmt: skip
"""Known codes, in order."""

KNOWN_CODES: frozenset[int] = frozenset(MUNICIPALITY_CODES)

FOREIGN_CODE = 888
"""Code for people born abroad. Single source (README of
bnorvinjosue/cedula-nicaragua-validator, April 2026, citing no regulation); it does not
appear in Law 152 or in the CSE registrar's manual."""

MAX_CODE = 640
"""Departments use blocks of 40 codes starting at 001; the last one ends at 640."""
