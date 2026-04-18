# Backend Foundation

## Local environment

Current verified baseline on this machine:
- Python 3.10.x

Recommended setup from repository root:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .[dev]
```

If `venv` was created without pip on your system, bootstrap it first and then rerun the commands above:

```bash
python3 -m ensurepip --upgrade
python -m pip install --upgrade pip setuptools wheel
```

## Run locally

```bash
. .venv/bin/activate
uvicorn app.main:app --app-dir backend --reload
```

Minimal import check:

```bash
. .venv/bin/activate
PYTHONPATH=backend python -c "from app.main import app; print(app.title)"
```

## Run tests

```bash
. .venv/bin/activate
pytest
```

## Seed initial admin

The backend reads these environment variables when seeding:

- `INITIAL_ADMIN_USERNAME`
- `INITIAL_ADMIN_PASSWORD`
- `INITIAL_ADMIN_EMAIL`
- `DATABASE_URL`

Run:

```bash
. .venv/bin/activate
PYTHONPATH=backend python -m app.scripts.seed_admin
```

Example:

```bash
INITIAL_ADMIN_USERNAME=admin \
INITIAL_ADMIN_PASSWORD='ChangeMe123!' \
INITIAL_ADMIN_EMAIL='admin@example.com' \
PYTHONPATH=backend .venv/bin/python -m app.scripts.seed_admin
```

## Notes

- Default DB is SQLite for local bootstrap; target architecture remains PostgreSQL.
- Current scope only includes backend foundation, auth, core models, role dependency, and base tests.
