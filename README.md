# DesklyCRM

[![CI](https://github.com/RezPoint/deskly-crm/actions/workflows/ci.yml/badge.svg)](https://github.com/RezPoint/deskly-crm/actions/workflows/ci.yml)
[![CodeQL](https://github.com/RezPoint/deskly-crm/actions/workflows/codeql.yml/badge.svg)](https://github.com/RezPoint/deskly-crm/actions/workflows/codeql.yml)
[![Release](https://img.shields.io/github/v/release/RezPoint/deskly-crm)](https://github.com/RezPoint/deskly-crm/releases)

DesklyCRM is a lightweight client & order manager for freelancers and small businesses вЂ” track requests, statuses, payments, and export reports in CSV.

## Why DesklyCRM
Keep your client work in one place: who requested what, whatвЂ™s in progress, whatвЂ™s paid, and whatвЂ™s done вЂ” without heavy CRMs.

## Features (MVP)
- **Clients directory** вЂ” contacts, notes, quick lookup
- **Orders tracking** вЂ” title, price, comments, linked client
- **Status workflow** вЂ” `new` / `in_progress` / `done` / `canceled`
- **Payments** вЂ” `paid` / `unpaid` (optional field for MVP)
- **CSV export** вЂ” download orders as a report
- **UI polish** — fast status edits, better empty states, validation hints

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
Health: http://127.0.0.1:8000/health
Metrics: http://127.0.0.1:8000/metrics
UI: http://127.0.0.1:8000/ui/clients

## Docker (Recommended)
```bash
docker compose up --build
```

Open in your browser: http://127.0.0.1:8000
Health: http://127.0.0.1:8000/health
Metrics: http://127.0.0.1:8000/metrics
UI: http://127.0.0.1:8000/ui/clients

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

## Observability
Environment variables:
- `LOG_LEVEL` (default: `INFO`)
- `APP_VERSION` (default: `0.0.0`)

Endpoints:
- `GET /health` returns `status`, `service`, `version`, `db`, `uptime_seconds`
- `GET /metrics` exposes Prometheus metrics

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
	вЂўv0.1 вЂ” clients + orders + statuses + CSV export
	вЂўv0.2 вЂ” authentication + user accounts
	вЂўv0.3 вЂ” reminders, filters, activity log
	вЂўv1.0 вЂ” deploy guide + stable UI

Contributing

Issues and pull requests are welcome. For major changes, please open an issue first to discuss what youвЂ™d like to add.

License

MIT License вЂ” see LICENSE.

