# DesklyCRM

[![CI](https://github.com/RezPoint/deskly-crm/actions/workflows/ci.yml/badge.svg)](https://github.com/RezPoint/deskly-crm/actions/workflows/ci.yml)
[![CodeQL](https://github.com/RezPoint/deskly-crm/actions/workflows/codeql.yml/badge.svg)](https://github.com/RezPoint/deskly-crm/actions/workflows/codeql.yml)
[![Release](https://img.shields.io/github/v/release/RezPoint/deskly-crm)](https://github.com/RezPoint/deskly-crm/releases)

DesklyCRM is a lightweight client and order manager for freelancers and small businesses - track requests, statuses, payments, reminders, and export reports in CSV.

## Why DesklyCRM
Keep your client work in one place: who requested what, what's in progress, what's paid, and what's done - without heavy CRMs.

## Features (MVP)
- **Clients directory** - contacts, notes, quick lookup
- **Orders tracking** - title, price, comments, linked client
- **Status workflow** - `new` / `in_progress` / `done` / `canceled`
- **Payments** - partial payments and balance tracking
- **CSV export** - download orders as a report
- **Reminders** - due dates and linked entities
- **Activity log** - audit trail for important actions

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

Open in your browser:
- http://127.0.0.1:8000/setup (first run only)
- http://127.0.0.1:8000/login
- http://127.0.0.1:8000/ui/clients

Health: http://127.0.0.1:8000/health
Metrics: http://127.0.0.1:8000/metrics

## Environment
Copy `.env.example` to `.env` and adjust values as needed.

Main variables:
- `DATABASE_URL` (defaults to SQLite)
- `JWT_SECRET`
- `JWT_EXPIRE_MINUTES`
- `LOG_LEVEL`
- `APP_VERSION`
- `MIGRATE_ON_START` (set to `1` to run migrations on startup)
- `AUTO_CREATE_DB` (set to `0` when using migrations in production)

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

PowerShell:
```bash
$env:DATABASE_URL="postgresql+psycopg://deskly:deskly@localhost:5432/desklycrm"
```

Command Prompt:
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
- `JWT_SECRET` (default: `dev-secret-change-me`)
- `JWT_EXPIRE_MINUTES` (default: `1440`)

Endpoints:
- `GET /health` returns `status`, `service`, `version`, `db`, `uptime_seconds`
- `GET /metrics` exposes Prometheus metrics

## Auth (0.2)
- First run: open `/setup` to create the owner account.
- `/setup` is available only when there are no users yet.
- Login via `/login` (web) or `POST /api/auth/login` (API).
- To add users, go to `/ui/users` as owner/admin.

API examples:
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"owner@example.com\",\"password\":\"secret123\"}"

curl -X POST http://127.0.0.1:8000/api/users \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"user@example.com\",\"password\":\"secret123\",\"role\":\"viewer\"}"
```

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
- v0.1 - clients + orders + statuses + CSV export
- v0.2 - authentication + user accounts
- v0.3 - reminders, filters, activity log
- v1.0 - deploy guide + stable UI

## Contributing

Issues and pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to add.

## License

MIT License - see LICENSE.
