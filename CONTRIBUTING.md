# Contributing

## Setting up the environment

```bash
uv sync                 # creates .venv with the development dependencies pinned in uv.lock
uv run pytest           # tests
uv run ruff check . && uv run ruff format --check .
uv run mypy             # strict mode
uv run pytest --cov     # branch coverage (minimum 95%)
```

CI runs exactly these commands with `uv sync --locked`. If you change a dependency, update `uv.lock` (`uv lock`) in the same pull request.

## Branches and pull requests (Git Flow)

| Branch | Target | PR title |
|--------|--------|----------|
| `feature/*` | `develop` | `feat(scope): add ...` |
| `bugfix/*` | `develop` | `fix(scope): ...` |
| `release/x.y.z` | `main` (then back-merge into `develop`) | `release: vx.y.z` |
| `hotfix/*` | `main` (then back-merge into `develop`) | `fix(scope): ...` |

PR titles in English ([Conventional Commits](https://www.conventionalcommits.org/)); PR descriptions in Spanish.

## Adding a document

1. Create a class in `src/stdnum_centroamerica/<country>/` that inherits from `BaseDocument`:
   - `_PATTERN`: the expression the compact form must match (compiled with `re.ASCII`; it is used with `fullmatch`).
   - `_check_content()`: additional rules (components, check digit); returns an `ErrorCode` or `None`.
   - If a pattern is not enough, override `_check()`. `_prepare()` changes the form that is validated.
   - `generate()` using `stdnum_centroamerica._random` (never the `random` module).
   - If the document has options: `__slots__`, keyword-only parameters, `_init_attr()` in the constructor and `_options()`.
2. Add the key to the catalog in `_registry.py`.
3. Add valid, invalid and formatting vectors to `tests/vectors/documents.json`, plus document-specific tests in `tests/`.
4. Add a row to the README table (a test compares it with `describe()`) and to `docs/sources.md`, with the source and the date it was consulted.
5. Add an entry to `CHANGELOG.md`.

## Sources

Every rule must cite a source in `docs/sources.md`, with the date it was consulted: "official" if it comes from the institution, "open" if it comes from open-source implementations. Numbers used in tests must be synthetic or examples published by the institution, never numbers of real people.
