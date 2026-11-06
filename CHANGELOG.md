# Changelog

All notable changes to this project are documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
