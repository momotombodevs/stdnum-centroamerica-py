# Installation

The package is published on PyPI as `stdnum-centroamerica` and imported as `stdnum_centroamerica`. It requires Python 3.11 or later and has no dependencies.

> Not to be confused with `python-stdnum`, which uses the `stdnum` module. This package never uses that name, so both can be installed side by side.

## With uv (recommended)

In a uv-managed project (updates `pyproject.toml` and `uv.lock`):

```bash
uv add stdnum-centroamerica
```

With an integration (extras can be combined: `[pydantic,django]`):

```bash
uv add "stdnum-centroamerica[pydantic]"   # FastAPI, Pydantic v2, SQLModel, Litestar
uv add "stdnum-centroamerica[django]"     # Django and Django REST Framework
uv add "stdnum-centroamerica[wtforms]"    # WTForms and Flask-WTF
```

In an existing virtual environment, without a `pyproject.toml`:

```bash
uv pip install stdnum-centroamerica
```

To try it without installing anything in your project:

```bash
uvx --with stdnum-centroamerica python -c "import stdnum_centroamerica as s; print(s.is_valid('sv.dui', '12345678-4'))"
```

## With pip

Always inside a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install stdnum-centroamerica
python -m pip install "stdnum-centroamerica[django]"
```

In `requirements.txt`:

```text
stdnum-centroamerica==0.1.0
```

## Poetry and PDM

```bash
poetry add stdnum-centroamerica
pdm add stdnum-centroamerica
```

## Production: pinned versions and hashes

Pin the exact version and verify hashes so the package cannot be substituted:

```bash
# uv: the lockfile already records hashes
uv lock && uv sync --locked

# pip: generate a requirements file with hashes and require them on install
uv pip compile pyproject.toml --generate-hashes -o requirements.txt
python -m pip install --require-hashes -r requirements.txt
```

Releases published from GitHub Actions carry attestations (PEP 740): the package page on PyPI shows the repository and workflow that published each file.

## From GitHub or a local checkout

Before a release, or to try a branch:

```bash
uv add "stdnum-centroamerica @ git+https://github.com/momotombodevs/stdnum-centroamerica-py@v0.1.0"
python -m pip install "stdnum-centroamerica @ git+https://github.com/momotombodevs/stdnum-centroamerica-py@v0.1.0"
```

In editable mode from another project on your machine:

```bash
uv add --editable ../stdnum-centroamerica-py
python -m pip install -e ../stdnum-centroamerica-py
```

## Verify the installation

```bash
python -c "import stdnum_centroamerica as s; print(s.__version__, len(s.keys()))"
# 0.1.0 18
```
