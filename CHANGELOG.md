# Changelog

All notable changes to this project are documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `sca.canonical(key, number)` and `canonical()` on every bundled document: the form to store. Variants of the same number share it and different numbers never do. It is the compact form, except in Panama, where it keeps the hyphens; Panama, `gt.nit` and `sv.nrc` also drop leading zeros (`8-0926-01601` is `8-926-1601`).
- `normalize="canonical"` in the Pydantic, Django and WTForms integrations.

### Changed
- The Pydantic `Document` and Django `DocumentFormField` now default to `normalize="canonical"` instead of `"compact"`. For Panama the output keeps its hyphens (`compact()` turned `1-12-345` and `11-2-345` into the same `112345`); for Panama, `gt.nit` and `sv.nrc` it also drops leading zeros. Every other document returns the same value as before.
- Numbers whose digits are all zero (`00000000-0`, `00`) are rejected with `COMPONENT`. In Panama, that means a zero volume and entry (`8-0-0`) or a zero order number (`E-8-0`), which also covers the DGI sheet templates `8-NT-000-00` and `PE-4-000-000`. `generate()` never produces them. Your own subclasses of `BaseDocument` inherit the rule; override `_is_placeholder()` to opt out.
- `describe()` reports `ni.cedula` as `Level.FORMAT`: the check letter is only verified with `strict_letter=True`.
- `UnknownDocumentError` only repeats the key when it looks like `country.document` (letters before the dot) and is at most 64 characters long. A document number passed as the key by mistake is no longer echoed.
- `register()` rejects keys longer than 64 characters.

### Fixed
- `mrz.td1` `parse()`: with an empty optional field on line 1 and data on line 2, `optional_data` started with the line-1 filler (`<<<<<<<<<<<<<<<AB123`); it is now `AB123`.

### Upgrading
- Panamanian numbers stored by 0.1.0 through the Pydantic or Django integrations are in compact form (`8PE3824523`), which cannot be turned back into the original reliably. Re-collect them, or recompute them from a source that kept the hyphens, and store `sca.canonical()` from now on.
- `gt.nit` and `sv.nrc` stored with leading zeros now have a different canonical form: run `sca.canonical()` over the column before adding a `UNIQUE` constraint.

### Security
- Docs: send numbers in request bodies, not URLs; use `hide_input_in_errors=True` in Pydantic models; the Django `ModelForm` pattern now normalizes before `max_length` applies.
- Release workflow: the tests run in their own job, and the build job pins `twine`.

## [0.1.0] - 2026-11-05

Initial release.

### Added
- 18 documents: `gt.nit`, `gt.dpi`, `sv.dui`, `sv.nit`, `sv.nrc`, `hn.identidad`, `hn.rtn`, `ni.cedula`, `ni.ruc`, `cr.cedula_fisica`, `cr.cedula_juridica`, `cr.dimex`, `cr.nite`, `pa.cedula`, `pa.ruc`, `mrz.td3`, `mrz.td1` and `mrz.td2`.
- API: `is_valid`, `validate` (with `ErrorCode`: `FORMAT`, `COMPONENT`, `CHECKSUM`), `make`, `parse`, `generate`, `keys`, `describe` and `register`.
- `parse()` for `ni.cedula` (with `birth_year_candidates()`), `hn.identidad`, `gt.dpi`, `pa.cedula` and the MRZ formats; results are immutable dataclasses that hide personal data from `repr()`.
- `strict_letter` and `strict_municipality` options for `ni.cedula`, off by default.
- Optional integrations: `contrib.pydantic.Document` (FastAPI, Pydantic v2), `contrib.django.DocumentValidator` and `DocumentFormField` (Django, DRF) and `contrib.wtforms.Document` (Flask-WTF), with the `[pydantic]`, `[django]` and `[wtforms]` extras.
- Security: input limited to 256 ASCII characters, linear regular expressions used with `fullmatch`, immutable instances, and numbers are never logged.
- Full type hints (`py.typed`), `mypy --strict`, ruff, Hypothesis property tests and tested examples in `examples/`.
