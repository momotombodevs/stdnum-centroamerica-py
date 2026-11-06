"""Basic usage, without frameworks.

Run:  uv run python examples/basic.py
"""

from __future__ import annotations

import stdnum_centroamerica as sca
from stdnum_centroamerica.ni import Cedula

MESSAGES = {
    sca.ErrorCode.FORMAT: "does not match the document format",
    sca.ErrorCode.COMPONENT: "contains a date or code that does not exist",
    sca.ErrorCode.CHECKSUM: "the check digit does not match",
}


def check(key: str, number: str, **options: bool) -> str:
    """Text to show to the user: the normalized number or the failure reason."""
    result = sca.validate(key, number, **options)
    if result.error is not None:
        return f"{key}: {MESSAGES[result.error]}"
    return f"{key}: valid ({sca.make(key).format(number)})"


def main() -> None:
    # 1. Validate and get the failure reason
    print(check("sv.dui", "12345678-4"))
    print(check("sv.dui", "12345678-5"))
    print(check("ni.cedula", "001-010190-0001A", strict_letter=True))

    # 2. Normalize for storage (compact) or display (format)
    dpi = sca.make("gt.dpi")
    print(
        "DPI compact:", dpi.compact("1234 56789 0101"), "| formatted:", dpi.format("1234567890101")
    )

    # 3. Read the components (personal data: do not write them to logs)
    cedula = sca.parse("ni.cedula", "001-010190-0001N")
    print(
        "Municipality:",
        cedula.municipality_code,
        "| possible years:",
        cedula.birth_year_candidates(),
    )

    # 4. Use a document class directly
    print("Check letter:", Cedula.check_letter("0010101900001"))

    # 5. Catalog and sample data
    for info in sca.describe():
        print(
            f"{info.key:<20} {info.country:<5} {info.level:<9} sample: {sca.generate(info.key)!r}"
        )


if __name__ == "__main__":
    main()
