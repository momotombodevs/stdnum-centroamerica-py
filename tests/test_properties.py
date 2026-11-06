"""Properties that hold for any input (Hypothesis)."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import stdnum_centroamerica as sca

KEYS = [info.key for info in sca.describe()]

# Inputs that look like real numbers: digits, letters, separators and MRZ filler.
document_like = st.text(alphabet="0123456789ABCDEFKNPEJRabcdkn<- \t\n", max_size=100)
any_text = st.text(max_size=300)


@pytest.mark.parametrize("key", KEYS)
@settings(max_examples=150, deadline=None)
@given(number=document_like | any_text)
def test_never_raises_and_always_returns_a_result(key: str, number: str) -> None:
    document = sca.make(key)
    result = document.validate(number)
    assert isinstance(result, sca.ValidationResult)
    assert result.is_valid == document.is_valid(number)
    assert isinstance(document.format(number), str)
    assert isinstance(document.compact(number), str)


@pytest.mark.parametrize("key", KEYS)
@settings(max_examples=150, deadline=None)
@given(number=document_like | any_text)
def test_format_and_compact_are_idempotent(key: str, number: str) -> None:
    document = sca.make(key)
    formatted = document.format(number)
    compact = document.compact(number)
    assert document.format(formatted) == formatted
    assert document.compact(compact) == compact


@pytest.mark.parametrize("key", KEYS)
@settings(max_examples=150, deadline=None)
@given(number=document_like)
def test_if_valid_its_formatted_form_is_too(key: str, number: str) -> None:
    document = sca.make(key)
    if document.is_valid(number):
        assert document.is_valid(document.format(number))


@pytest.mark.parametrize("key", [k for k in KEYS if not k.startswith("pa.")])
@settings(max_examples=100, deadline=None)
@given(data=st.data())
def test_if_valid_its_compact_form_is_too(key: str, data: st.DataObject) -> None:
    # In Panama the hyphens are part of the number: the compact form cannot be validated.
    number = sca.generate(key)
    document = sca.make(key)
    decorated = data.draw(st.sampled_from([number, f" {number} ", number.lower()]))
    assert document.is_valid(document.compact(decorated))


@pytest.mark.parametrize("key", [k for k in KEYS if isinstance(sca.make(k), sca.SupportsParse)])
@settings(max_examples=150, deadline=None)
@given(number=document_like | any_text)
def test_parse_returns_none_iff_invalid(key: str, number: str) -> None:
    assert (sca.parse(key, number) is None) == (not sca.is_valid(key, number))


@pytest.mark.parametrize("key", KEYS)
@settings(max_examples=50, deadline=None)
@given(data=st.data())
def test_generated_numbers_validate_with_whitespace_and_lowercase(
    key: str, data: st.DataObject
) -> None:
    number = sca.generate(key)
    padding = data.draw(st.text(alphabet=" \t\n\r", max_size=5))
    assert sca.is_valid(key, padding + number.lower() + padding)
