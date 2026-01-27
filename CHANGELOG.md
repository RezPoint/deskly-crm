# Changelog

## [0.1.3] - 2026-01-26
### Added
- Dockerfile, docker-compose, and .dockerignore for containerized dev.
- UI delete actions for clients, orders, and payments with confirmation prompts.
- Delete API endpoints for clients, orders, and payments.
- Additional tests for delete flows, UI flows, and decimal handling.

### Fixed
- Money calculations now normalize Decimal/float values to avoid SQLite float issues.
- UI TemplateResponse signature updated to avoid Starlette deprecation warnings.
- Client creation now handles unique constraint races with a 409 response.

## [0.1.4] - 2026-01-26
### Fixed
- CI smoke test aligned with numeric JSON responses for money fields.

## [0.1.5] - 2026-01-26
### Added
- PostgreSQL support via psycopg, Docker Compose Postgres service.
- Alembic migrations with initial schema.
- Pagination, sorting, and date filters for orders.
- CSV export filters and UI export links.
- UI totals for orders and formatted dates.

### Fixed
- Unified UI error styling and empty states.

## [0.3.1] - 2026-01-27
### Added
- Invite flow (API + UI).

### Fixed
- Invite migration idempotency for existing tables.

## [0.3.0] - 2026-01-27
### Added
- Tenants table and workspace setup flow.
- Tenant UI page and API endpoint.

### Fixed
- Postgres alembic version length for long revision IDs.

## [0.2.8] - 2026-01-27
### Added
- Tenant scoping fields across core entities (clients, orders, payments, reminders, users, activity).

### Fixed
- Tenant filtering for UI/API lists, exports, and imports.

## [0.1.6] - 2026-01-26
### Added
- Indexes for filters and search (clients name, orders status/created_at/title/comment).
- Optional Alembic migrations on startup via `MIGRATE_ON_START=1`.
- Export search filter for orders (`q`).

### Fixed
- Date range validation for orders and export endpoints.
- Docker image now includes Alembic files for migrations.
