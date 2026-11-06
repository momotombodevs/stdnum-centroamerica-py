"""The ``>>>`` examples in the README and the docstrings run as written."""

from __future__ import annotations

import doctest
from pathlib import Path

import stdnum_centroamerica

ROOT = Path(__file__).parents[1]


def test_readme_examples() -> None:
    result = doctest.testfile(
        str(ROOT / "README.md"), module_relative=False, optionflags=doctest.ELLIPSIS
    )
    assert result.attempted > 20
    assert result.failed == 0


def test_docstring_examples() -> None:
    result = doctest.testmod(stdnum_centroamerica)
    assert result.attempted > 0
    assert result.failed == 0
