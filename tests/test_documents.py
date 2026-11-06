"""Shared contract of the 18 documents, using ``tests/vectors/documents.json``."""

from __future__ import annotations

import pytest

import stdnum_centroamerica as sca
from tests.conftest import VECTORS


def _cases(kind: str) -> list[object]:
    return [
        pytest.param(key, case["number"], id=f"{key}: {case['id']!r}")
        for key, entry in VECTORS.items()
        for case in entry[kind]
    ]


def _formats() -> list[object]:
    return [
        pytest.param(key, case["input"], case["expected"], id=f"{key}: {case['input']!r}")
        for key, entry in VECTORS.items()
        for case in entry["formats"]
    ]


VALID = _cases("valid")
INVALID = _cases("invalid")
INVALID_WITH_ERROR = [
    pytest.param(key, case["number"], case["error"], id=f"{key}: {case['id']!r}")
    for key, entry in VECTORS.items()
    for case in entry["invalid"]
]


def test_every_document_has_vectors() -> None:
    assert set(VECTORS) == set(sca.keys())


@pytest.mark.parametrize(("key", "number"), VALID)
def test_accepts_valid_numbers(key: str, number: str) -> None:
    assert sca.is_valid(key, number)


@pytest.mark.parametrize(("key", "number"), INVALID)
def test_rejects_invalid_numbers(key: str, number: str) -> None:
    assert not sca.is_valid(key, number)


@pytest.mark.parametrize(("key", "number"), VALID)
def test_validate_reports_no_error_for_valid_numbers(key: str, number: str) -> None:
    result = sca.validate(key, number)
    assert result.is_valid
    assert result.error is None
    assert result


@pytest.mark.parametrize(("key", "number", "error"), INVALID_WITH_ERROR)
def test_validate_reports_the_expected_error(key: str, number: str, error: str) -> None:
    # The reason matters: a vector meant to test a component must not pass on its checksum.
    result = sca.validate(key, number)
    assert not result.is_valid
    assert result.error is sca.ErrorCode(error)
    assert not result


@pytest.mark.parametrize(("key", "number"), VALID)
def test_ignores_surrounding_whitespace(key: str, number: str) -> None:
    assert sca.is_valid(key, f" \t{number}\n ")


@pytest.mark.parametrize(("key", "number"), VALID)
def test_is_case_insensitive(key: str, number: str) -> None:
    assert sca.is_valid(key, number.lower())
    assert sca.is_valid(key, number.upper())


@pytest.mark.parametrize(("key", "number"), VALID)
def test_rejects_unsupported_separators(key: str, number: str) -> None:
    compact = sca.make(key).compact(number)
    for separator in (".", "/", "_"):
        assert not sca.is_valid(key, compact[:1] + separator + compact[1:]), separator


@pytest.mark.parametrize(("key", "number"), VALID)
def test_formatted_number_stays_valid(key: str, number: str) -> None:
    document = sca.make(key)
    assert document.is_valid(document.format(number))


@pytest.mark.parametrize(("key", "number"), VALID + INVALID)
def test_format_and_compact_are_idempotent(key: str, number: str) -> None:
    document = sca.make(key)
    formatted = document.format(number)
    compact = document.compact(number)
    assert document.format(formatted) == formatted
    assert document.compact(compact) == compact


@pytest.mark.parametrize(("key", "number"), VALID)
def test_validate_and_is_valid_agree(key: str, number: str) -> None:
    document = sca.make(key)
    for candidate in (number, number + "0", number[:-1]):
        assert document.is_valid(candidate) == document.validate(candidate).is_valid


@pytest.mark.parametrize(("key", "given", "expected"), _formats())
def test_formats_and_compacts(key: str, given: str, expected: str) -> None:
    document = sca.make(key)
    assert document.format(given) == expected
    assert document.compact(given) == document.compact(expected)


@pytest.mark.parametrize("key", sorted(VECTORS))
def test_compact_strips_whitespace_and_hyphens_and_uppercases(key: str) -> None:
    assert sca.make(key).compact(" a-b\tc\nd\re\ff\vg ") == "ABCDEFG"


@pytest.mark.parametrize("key", sorted(VECTORS))
def test_rejects_non_str_types(key: str) -> None:
    document = sca.make(key)
    for value in (None, 123, b"123", ["1"]):
        with pytest.raises(TypeError, match="expected str"):
            document.is_valid(value)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            document.compact(value)  # type: ignore[arg-type]
