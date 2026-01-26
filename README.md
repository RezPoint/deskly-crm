# DesklyCRM

[![CI](https://github.com/RezPoint/deskly-crm/actions/workflows/ci.yml/badge.svg)](https://github.com/RezPoint/deskly-crm/actions/workflows/ci.yml)
[![CodeQL](https://github.com/RezPoint/deskly-crm/actions/workflows/codeql.yml/badge.svg)](https://github.com/RezPoint/deskly-crm/actions/workflows/codeql.yml)
[![Release](https://img.shields.io/github/v/release/RezPoint/deskly-crm)](https://github.com/RezPoint/deskly-crm/releases)

DesklyCRM is a lightweight client & order manager for freelancers and small businesses — track requests, statuses, payments, and export reports in CSV.

## Why DesklyCRM
Keep your client work in one place: who requested what, what’s in progress, what’s paid, and what’s done — without heavy CRMs.

## Features (MVP)
- **Clients directory** — contacts, notes, quick lookup
- **Orders tracking** — title, price, comments, linked client
- **Status workflow** — `new` / `in_progress` / `done` / `canceled`
- **Payments** — `paid` / `unpaid` (optional field for MVP)
- **CSV export** — download orders as a report

## Tech Stack
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL (recommended) / SQLite (local default)
- **UI:** Jinja2 templates (simple web interface)

## Quick Start
> Requirements: Python 3.10+

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open in your browser: http://127.0.0.1:8000

## Docker (Recommended)
```bash
docker compose up --build
```

Open in your browser: http://127.0.0.1:8000

## PostgreSQL (Local)
Set `DATABASE_URL` to use Postgres:
```bash
set DATABASE_URL=postgresql+psycopg://deskly:deskly@localhost:5432/desklycrm
```

## Database Migrations
Alembic is available for schema migrations.
```bash
alembic upgrade head
```

To create new migrations:
```bash
alembic revision --autogenerate -m "describe change"
```

If you use migrations in production, set `AUTO_CREATE_DB=0` to avoid `create_all`.
PostgreSQL users should run migrations after changing `DATABASE_URL`.
You can also run migrations on startup by setting `MIGRATE_ON_START=1`.

## Development
```bash
python -m pytest -q
```

## Project Structure
```txt
deskly-crm/
  app/
    main.py
    db.py
    models.py
    schemas.py
    routes/
      clients.py
      orders.py
    templates/
      index.html
      clients.html
      orders.html
  tests/
  requirements.txt
  README.md
  LICENSE
```

## Roadmap
	•v0.1 — clients + orders + statuses + CSV export
	•v0.2 — authentication + user accounts
	•v0.3 — reminders, filters, activity log
	•v1.0 — deploy guide + stable UI

Contributing

Issues and pull requests are welcome. For major changes, please open an issue first to discuss what you’d like to add.

License

MIT License — see LICENSE.

