# stdnum-centroamerica

[![ci](https://github.com/momotombodevs/stdnum-centroamerica-py/actions/workflows/ci.yml/badge.svg)](https://github.com/momotombodevs/stdnum-centroamerica-py/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/stdnum-centroamerica)](https://pypi.org/project/stdnum-centroamerica/)
[![Python](https://img.shields.io/pypi/pyversions/stdnum-centroamerica)](pyproject.toml)
[![License](https://img.shields.io/pypi/l/stdnum-centroamerica)](LICENSE)

Validate, format and compact Central American identity and tax document numbers: DPI, NIT, DUI, NRC, RTN, cédulas, RUC, DIMEX and passport MRZs. No dependencies, fully typed, Python 3.11 or later. Works in any project: scripts, FastAPI, Flask, Django, DRF, Celery or notebooks.

## Installation

With [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv add stdnum-centroamerica
uv add "stdnum-centroamerica[pydantic]"   # FastAPI / Pydantic v2 integration
uv add "stdnum-centroamerica[django]"     # Django / DRF integration
uv add "stdnum-centroamerica[wtforms]"    # Flask-WTF / WTForms integration
```

With pip, inside a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install stdnum-centroamerica
python -m pip install "stdnum-centroamerica[django]"
```

More options (Poetry, PDM, installing from GitHub, editable mode, hashes) in [docs/installation.md](docs/installation.md).

## Usage

Each document has a `country.document` key (`ni.cedula`, `gt.dpi`, ...) and three operations: validate, format and compact.

```pycon
>>> import stdnum_centroamerica as sca

>>> sca.is_valid("ni.cedula", "001-010190-0001N")
True
>>> sca.is_valid("ni.ruc", "J0310000000001")          # legal entity
True
>>> sca.is_valid("ni.ruc", "0000300766011M")          # a RUC cannot start with four zeros
False

>>> sca.make("ni.cedula").format("0010101900001n")
'001-010190-0001N'
>>> sca.make("ni.cedula").compact("001-010190-0001n")
'0010101900001N'
>>> sca.make("gt.dpi").format("1234567890101")
'1234 56789 0101'

```

`validate()` also returns the reason for a failure, which is useful for error messages:

```pycon
>>> result = sca.validate("sv.dui", "12345678-5")
>>> result.is_valid
False
>>> result.error
<ErrorCode.CHECKSUM: 'checksum'>
>>> bool(sca.validate("sv.dui", "12345678-4"))
True

```

| `ErrorCode` | Value | Meaning |
|-------------|-------|---------|
| `FORMAT` | `"format"` | wrong length, characters or structure |
| `COMPONENT` | `"component"` | a component (date, department, municipality, prefix) is out of range |
| `CHECKSUM` | `"checksum"` | the check digit or letter does not match |

`ErrorCode` is a `StrEnum`, so it serializes to JSON as plain text.

### Options

The Nicaraguan cédula does not check its letter by default, because the CSE does not publish the formula (modulo 23, from unofficial sources). Options are passed as keyword arguments:

```pycon
>>> sca.is_valid("ni.cedula", "001-010190-0001A")                      # the correct letter is N
True
>>> sca.is_valid("ni.cedula", "001-010190-0001A", strict_letter=True)
False
>>> sca.is_valid("ni.cedula", "282-010190-0001A", strict_municipality=True)   # 282 is not in the list
False

```

The document classes can also be used directly:

```pycon
>>> from stdnum_centroamerica.ni import Cedula
>>> Cedula(strict_municipality=True).is_valid("001-010190-0001N")
True
>>> Cedula.check_letter("0010101900001")
'N'

```

A misspelled option raises `TypeError` instead of being silently ignored.

### Parsing components

`parse()` reads the components encoded in the number and returns an immutable object, or `None` if the number is not valid. It is available for `ni.cedula`, `hn.identidad`, `gt.dpi`, `pa.cedula` and the three MRZ formats.

```pycon
>>> cedula = sca.parse("ni.cedula", "001-010190-0001N")
>>> cedula.municipality_code, cedula.birth_day, cedula.birth_month, cedula.birth_year_two_digits
(1, 1, 1, 90)
>>> import datetime
>>> cedula.birth_year_candidates(datetime.date(2026, 11, 5))
(1990,)

>>> sca.parse("hn.identidad", "0906-1990-00001").municipality_code
6
>>> sca.parse("gt.dpi", "1234 56789 0101").department_code
1
>>> sca.parse("pa.cedula", "PE-5-687").kind
<CedulaKind.BORN_ABROAD: 'born_abroad'>

>>> mrz = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\nL898902C36UTO7408122F1204159ZE184226B<<<<<10"
>>> sca.is_valid("mrz.td3", mrz)
True
>>> sca.parse("mrz.td3", mrz).surname
'ERIKSSON'

```

The number does not encode the century, so `birth_year_candidates()` returns the possible years (it may be empty: 29/02/01 exists neither in 1901 nor in 2001). For the same reason it cannot be used to decide legal age: someone born in 2010 also gets the candidate 1910.

Components come from the structure of the number and are not checked against any registry. **Birth dates and the other components are personal data**: they are hidden from `repr()` so they do not end up in a log by accident, but treat them accordingly (see [docs/security.md](docs/security.md)).

### Test data

`generate()` returns a synthetic valid number, useful for fixtures and sample data. It is random and may match a real number by chance: do not use it as data about people.

```pycon
>>> sca.is_valid("gt.dpi", sca.generate("gt.dpi"))
True

```

### Catalog and custom documents

```pycon
>>> len(sca.keys())
18
>>> info = sca.describe()[0]
>>> info.key, info.country, info.name, info.level
('gt.nit', 'GT', 'NIT', <Level.COMPLETE: 'complete'>)

```

An unknown key raises `UnknownDocumentError` (with suggestions when it resembles an existing key). `sca.register(key, cls)` adds or replaces a document; the class must implement the `Document` protocol (`is_valid`, `validate`, `format`, `compact`). Call it at application startup.

## Supported documents

**complete** = validates format and check digit; **format** = validates length, characters and basic ranges.

| Country | Document | Key | Level |
|---------|----------|-----|-------|
| Guatemala | NIT | `gt.nit` | complete |
| Guatemala | DPI (CUI) | `gt.dpi` | complete (check digit and department) |
| El Salvador | DUI | `sv.dui` | complete |
| El Salvador | NIT | `sv.nit` | complete (also accepts the 9-digit DUI) |
| El Salvador | NRC | `sv.nrc` | format |
| Honduras | Número de identidad | `hn.identidad` | format (valid department and municipality) |
| Honduras | RTN | `hn.rtn` | format |
| Nicaragua | Cédula | `ni.cedula` | complete (check letter with `strict_letter`, off by default) |
| Nicaragua | RUC | `ni.ruc` | format |
| Costa Rica | Cédula física | `cr.cedula_fisica` | format |
| Costa Rica | Cédula jurídica | `cr.cedula_juridica` | format |
| Costa Rica | DIMEX | `cr.dimex` | format |
| Costa Rica | NITE | `cr.nite` | format |
| Panama | Cédula | `pa.cedula` | format |
| Panama | RUC | `pa.ruc` | format (the DV is not validated) |
| International | Passport MRZ (TD3) | `mrz.td3` | complete (ICAO 9303) |
| International | ID card MRZ (TD1) | `mrz.td1` | complete (ICAO 9303) |
| International | ID document MRZ (TD2) | `mrz.td2` | complete (ICAO 9303) |

Notes:

- **Panama:** volume and entry have variable length, so the number can only be read with its hyphens. Use `format()` for the canonical form (`8-926-1601`); `compact()` removes the hyphens.
- **Honduras:** `hn.identidad` accepts the special codes for naturalized citizens (`0890`) and dual nationality (`0880`).
- **MRZ:** accepted with or without line breaks. Dates stay as `YYMMDD`, because the century cannot be inferred. Country-specific passport numbers are not validated, only the MRZ.
- **Nicaragua:** the municipality codes and the check letter come from third parties (the CSE does not publish them), and code 888 has a single source. In Panama, provinces 10 to 13 and the PI and AV suffixes are not official either.
- The source of every rule, with the date it was consulted, is in [docs/sources.md](docs/sources.md).

## Framework integrations

The core works in any project with no configuration. The integrations are optional and report errors in each framework's own format. Their messages default to English and can be overridden (see each guide).

**FastAPI / Pydantic v2** ([guide](docs/fastapi.md)):

```python
from typing import Annotated
from pydantic import BaseModel
from stdnum_centroamerica.contrib.pydantic import Document

Dpi = Annotated[str, Document("gt.dpi")]  # validates and stores it compact

class Customer(BaseModel):
    dpi: Dpi
    cedula: Annotated[str, Document("ni.cedula", normalize="format", strict_letter=True)]
# When invalid, FastAPI responds with 422 and type="stdnum_checksum" (or format / component).
```

**Django and DRF** ([guide](docs/django.md)):

```python
from stdnum_centroamerica.contrib.django import DocumentFormField, DocumentValidator

class Customer(models.Model):
    dpi = models.CharField(max_length=13, validators=[DocumentValidator("gt.dpi")])

class CustomerForm(forms.Form):
    dpi = DocumentFormField("gt.dpi")  # cleaned_data["dpi"] is compact
```

**Flask** ([guide](docs/flask.md)):

```python
from stdnum_centroamerica.contrib.wtforms import Document

class CustomerForm(FlaskForm):
    dpi = StringField("DPI", validators=[DataRequired(), Document("gt.dpi")])
```

Complete, tested examples in [examples/](examples/).

## Security

- No dependencies, no network access and no I/O: the package never stores or logs numbers.
- Only `str` inputs of up to 256 ASCII characters are accepted; anything else is a `FORMAT` error and no regular expression runs. This rejects digits from other scripts, Unicode hyphens and invisible spaces.
- Regular expressions run in linear time (no catastrophic backtracking), and the tests check this with adversarial inputs.
- Instances and data tables are immutable, so they can be shared between threads.

Details and recommendations for integrators in [docs/security.md](docs/security.md). To report a vulnerability, see [SECURITY.md](SECURITY.md).

## Development

```bash
uv sync
uv run pytest                    # tests (including Hypothesis property tests)
uv run ruff check . && uv run ruff format --check .
uv run mypy                      # strict mode
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the branching model and how to add a document.

## License

MIT
