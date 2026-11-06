"""Security rules: input size, Unicode tricks, bounded time and personal data."""

from __future__ import annotations

import time

import pytest

import stdnum_centroamerica as sca

KEYS = [info.key for info in sca.describe()]

VALID = {
    "gt.nit": "1234567-9",
    "gt.dpi": "1234567890101",
    "sv.dui": "12345678-4",
    "sv.nit": "0614-130386-136-4",
    "sv.nrc": "123456-7",
    "hn.identidad": "0801-1990-12345",
    "hn.rtn": "08011990123456",
    "ni.cedula": "001-010190-0001N",
    "ni.ruc": "J0310000000001",
    "cr.cedula_fisica": "1-0123-0456",
    "cr.cedula_juridica": "3-101-123456",
    "cr.dimex": "155812345678",
    "cr.nite": "1234567890",
    "pa.cedula": "8-926-1601",
    "pa.ruc": "8-NT-000-00",
    "mrz.td3": "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<L898902C36UTO7408122F1204159ZE184226B<<<<<10",
    "mrz.td1": "I<UTOD231458907<<<<<<<<<<<<<<<7408122F1204159UTO<<<<<<<<<<<6ERIKSSON<<ANNA<MARIA<<<<<<<<<<",
    "mrz.td2": "I<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<D231458907UTO7408122F1204159<<<<<<<6",
}


def test_one_valid_number_per_document() -> None:
    assert set(VALID) == set(KEYS)
    for key, number in VALID.items():
        assert sca.is_valid(key, number), key


@pytest.mark.parametrize("key", KEYS)
def test_huge_input_is_rejected_quickly(key: str) -> None:
    huge = "1" * 1_000_000
    start = time.perf_counter()
    for _ in range(100):
        assert sca.validate(key, huge).error is sca.ErrorCode.FORMAT
    assert time.perf_counter() - start < 0.5


@pytest.mark.parametrize("key", KEYS)
def test_input_at_the_length_limit(key: str) -> None:
    number = VALID[key]
    padded = number.center(sca.MAX_INPUT_LENGTH)
    assert sca.is_valid(key, padded)
    assert not sca.is_valid(key, padded + " ")


@pytest.mark.parametrize("key", KEYS)
@pytest.mark.parametrize(
    "trick",
    [
        pytest.param(
            str.maketrans(
                "0123456789", "\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669"
            ),
            id="digitos-arabes",
        ),
        pytest.param(
            str.maketrans(
                "0123456789", "\uff10\uff11\uff12\uff13\uff14\uff15\uff16\uff17\uff18\uff19"
            ),
            id="digitos-anchos",
        ),
        pytest.param(str.maketrans("-", "\u2010"), id="guion-unicode"),
        pytest.param(str.maketrans("-", "\u2212"), id="signo-menos"),
    ],
)
def test_unicode_lookalikes_are_rejected(key: str, trick: dict[int, str]) -> None:
    number = VALID[key]
    tricked = number.translate(trick)
    if tricked != number:
        assert sca.validate(key, tricked).error is sca.ErrorCode.FORMAT


@pytest.mark.parametrize("key", KEYS)
@pytest.mark.parametrize("invisible", ["\u200b", "\u00a0", "\ufeff", "\u3000"])
def test_invisible_spaces_are_rejected(key: str, invisible: str) -> None:
    number = VALID[key]
    assert not sca.is_valid(key, invisible + number)
    assert not sca.is_valid(key, number[:2] + invisible + number[2:])


def test_letters_that_change_when_uppercased() -> None:
    # "\u0131".upper() == "I" and "ß".upper() == "SS": they must not make input valid.
    assert not sca.is_valid("ni.ruc", "J0310000000001".replace("J", "\u0237"))
    assert sca.make("gt.nit").compact("ß") == "ß"
    assert not sca.is_valid("mrz.td3", VALID["mrz.td3"].replace("ANNA", "ANN\u0131"))


@pytest.mark.parametrize("key", KEYS)
def test_trailing_newline_does_not_change_the_result(key: str) -> None:
    for candidate in ("X", "1", VALID[key][:-1]):
        assert sca.is_valid(key, candidate + "\n") == sca.is_valid(key, candidate)


@pytest.mark.parametrize("key", KEYS)
def test_adversarial_inputs_finish_in_bounded_time(key: str) -> None:
    adversarial = [
        "1-" * 127,
        "-" * 256,
        "PE-" * 85,
        "8-PI-" * 51,
        "<" * 256,
        "A" * 256,
        "1" * 255 + "X",
    ]
    start = time.perf_counter()
    for _ in range(50):
        for text in adversarial:
            sca.validate(key, text)
            sca.make(key).format(text)
    assert time.perf_counter() - start < 1.0


def test_component_repr_hides_personal_data() -> None:
    cedula = repr(sca.parse("ni.cedula", "001-251075-0012S"))
    assert "25" not in cedula.replace("municipality_code=1", "")
    assert "0012" not in cedula
    identidad = repr(sca.parse("hn.identidad", "0801-1990-12345"))
    assert "1990" not in identidad
    assert "12345" not in identidad
    assert "12345678" not in repr(sca.parse("gt.dpi", "1234567890101"))
    panama = repr(sca.parse("pa.cedula", "8-926-1601"))
    assert "926" not in panama
    assert "1601" not in panama


def test_error_messages_never_include_the_number() -> None:
    secret = "001-010190-0001N"
    with pytest.raises(sca.UnsupportedOperationError) as error:
        sca.parse("gt.nit", secret)
    assert secret not in str(error.value)

    with pytest.raises(TypeError) as type_error:
        sca.is_valid("ni.cedula", 10101900001)  # type: ignore[arg-type]
    assert "10101900001" not in str(type_error.value)


def test_data_tables_are_read_only() -> None:
    from stdnum_centroamerica._data import honduras, nicaragua

    with pytest.raises(TypeError):
        honduras.MUNICIPALITIES_BY_DEPARTMENT[19] = 1  # type: ignore[index]
    with pytest.raises(AttributeError):
        honduras.SPECIAL_CODES.add("0999")  # type: ignore[attr-defined]
    with pytest.raises(AttributeError):
        nicaragua.KNOWN_CODES.add(999)  # type: ignore[attr-defined]


def test_shared_documents_are_read_only() -> None:
    shared = sca.make("ni.cedula")
    with pytest.raises(AttributeError, match="immutable"):
        shared._strict_letter = True  # type: ignore[attr-defined]
    with pytest.raises(AttributeError, match="immutable"):
        shared.nuevo = 1  # type: ignore[attr-defined]
