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
