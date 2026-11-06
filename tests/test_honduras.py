"""Honduras identidad and RTN."""

from __future__ import annotations

import datetime
from collections.abc import Callable

from stdnum_centroamerica import ErrorCode
from stdnum_centroamerica._data.honduras import MUNICIPALITIES_BY_DEPARTMENT, SPECIAL_CODES
from stdnum_centroamerica.hn import Identidad, Rtn


def test_formats_and_compacts() -> None:
    doc = Identidad()
    assert doc.format("0801199012345") == "0801-1990-12345"
    assert doc.compact("0801-1990-12345") == "0801199012345"


def test_298_municipalities_in_18_departments() -> None:
    assert len(MUNICIPALITIES_BY_DEPARTMENT) == 18
    assert sum(MUNICIPALITIES_BY_DEPARTMENT.values()) == 298
    assert {"0880", "0890"} == SPECIAL_CODES


def test_first_and_last_municipality_of_each_department() -> None:
    doc = Identidad()
    for department, count in MUNICIPALITIES_BY_DEPARTMENT.items():
        first = f"{department:02d}01199012345"
        last = f"{department:02d}{count:02d}199012345"
        over = f"{department:02d}{count + 1:02d}199012345"
        assert doc.is_valid(first), first
        assert doc.is_valid(last), last
        assert not doc.is_valid(over), over


def test_accepts_every_department_and_municipality() -> None:
    doc = Identidad()
    rtn = Rtn()
    for department, municipalities in MUNICIPALITIES_BY_DEPARTMENT.items():
        for municipality in range(1, municipalities + 1):
            number = f"{department:02d}{municipality:02d}198500001"
            assert doc.is_valid(number), number
            assert rtn.is_valid(number + "7"), number


def test_registration_year_cannot_be_in_the_future(
    freeze_today: Callable[[datetime.date], None],
) -> None:
    freeze_today(datetime.date(2026, 11, 5))
    assert Identidad().is_valid("0801-2026-00001")
    assert Identidad().validate("0801-2027-00001").error is ErrorCode.COMPONENT
    assert Identidad().is_valid("0801-1800-00001")
    assert Identidad().validate("0801-1799-00001").error is ErrorCode.COMPONENT


def test_special_codes_need_no_municipality() -> None:
    assert Identidad().is_valid("0880-2015-00001")
    assert Identidad().is_valid("0890-2010-00012")
    assert not Identidad().is_valid("0870-2010-00012")
