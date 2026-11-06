"""Properties that hold for any input (Hypothesis)."""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import stdnum_centroamerica as sca
from tests.conftest import VECTORS

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


# -- valid inputs ---------------------------------------------------------------------------
# Random text is almost never a valid number, so the properties of valid numbers get their
# own strategy: a valid number (official vectors plus generated ones, fixed at import so
# Hypothesis can replay a failure) written with random case and separators.

_POOL = {
    key: [case["number"] for case in VECTORS[key]["valid"]] + [sca.generate(key) for _ in range(20)]
    for key in KEYS
}


@st.composite
def written_like_a_person(draw: st.DrawFn, key: str) -> tuple[str, str]:
    """Return ``(original, variant)``: the same valid number, written differently."""
    original = draw(st.sampled_from(_POOL[key]))
    if key.startswith("mrz."):
        lines = original.split("\n") if "\n" in original else [original]
        separator = draw(st.sampled_from(["\n", "\r\n", " \n", ""]))
        variant = separator.join(lines)
    elif key.startswith("pa."):
        groups = sca.make(key).format(original).split("-")
        variant = groups[0]
        for group in groups[1:]:
            variant += draw(st.sampled_from(["-", " ", " - ", "--", "\t"])) + group
    else:
        variant = ""
        for char in sca.make(key).compact(original):
            variant += draw(st.sampled_from(["", "", "", "-", " "])) + char
    flips = draw(st.lists(st.booleans(), min_size=len(variant), max_size=len(variant)))
    variant = "".join(c.lower() if flip else c for c, flip in zip(variant, flips, strict=True))
    padding = draw(st.text(alphabet=" \t\n", max_size=3))
    return original, padding + variant + padding


@pytest.mark.parametrize("key", KEYS)
@settings(max_examples=100, deadline=None)
@given(data=st.data())
def test_valid_numbers_stay_valid_however_they_are_written(key: str, data: st.DataObject) -> None:
    original, variant = data.draw(written_like_a_person(key))
    document = sca.make(key)
    assert document.is_valid(variant), variant
    assert document.is_valid(document.format(variant))
    assert document.format(variant) == document.format(original)


@pytest.mark.parametrize("key", KEYS)
@settings(max_examples=100, deadline=None)
@given(data=st.data())
def test_canonical_form_is_valid_stable_and_shared_by_variants(
    key: str, data: st.DataObject
) -> None:
    original, variant = data.draw(written_like_a_person(key))
    canonical = sca.canonical(key, variant)
    assert canonical == sca.canonical(key, original)
    assert sca.canonical(key, canonical) == canonical
    assert sca.is_valid(key, canonical), canonical


@pytest.mark.parametrize("key", [k for k in KEYS if isinstance(sca.make(k), sca.SupportsParse)])
@settings(max_examples=100, deadline=None)
@given(data=st.data())
def test_parse_reads_the_same_data_however_it_is_written(key: str, data: st.DataObject) -> None:
    original, variant = data.draw(written_like_a_person(key))
    parsed = sca.parse(key, variant)
    assert parsed is not None
    assert parsed == sca.parse(key, original)
