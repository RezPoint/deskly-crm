# DesklyCRM

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
- **Database:** SQLite
- **UI:** Jinja2 templates (simple web interface)

## Quick Start
> Requirements: Python 3.10+

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open in your browser: http://127.0.0.1:8000

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
	•v1.0 — Docker + deploy guide + stable UI

Contributing

Issues and pull requests are welcome. For major changes, please open an issue first to discuss what you’d like to add.

License

MIT License — see LICENSE.

