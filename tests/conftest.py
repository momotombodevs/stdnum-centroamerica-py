"""Fixtures and helpers shared by the tests."""

from __future__ import annotations

import datetime
import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

from stdnum_centroamerica import _dates, _registry

VECTORS_PATH = Path(__file__).parent / "vectors" / "documents.json"


def load_vectors() -> dict[str, Any]:
    """Valid, invalid and formatting cases of each document."""
    data: dict[str, Any] = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
    return data["documents"]  # type: ignore[no-any-return]


VECTORS = load_vectors()


@pytest.fixture
def freeze_today(monkeypatch: pytest.MonkeyPatch) -> Callable[[datetime.date], None]:
    """Freeze the "today" used by Honduras and ``birth_year_candidates()``."""

    def freeze(day: datetime.date) -> None:
        monkeypatch.setattr(_dates, "today", lambda: day)

    return freeze


@pytest.fixture
def clean_registry() -> Iterator[None]:
    """Remove, after the test, any document the test registered."""
    before = set(_registry._custom)
    yield
    for key in set(_registry._custom) - before:
        _registry._unregister(key)
