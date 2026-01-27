POSTGRES_URL ?= postgresql+psycopg://deskly:deskly@localhost:5432/desklycrm

dev:
	pip install -r requirements.txt
	PYTHONPATH=. DATABASE_URL=$(POSTGRES_URL) uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-clean:
	powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force }"
	$(MAKE) dev

lint:
	python -m compileall app

test:
	python -m compileall app	

migrate:
	PYTHONPATH=. DATABASE_URL=$(POSTGRES_URL) alembic upgrade head

revision:
	@if [ -z "$(MSG)" ]; then echo "MSG is required, e.g. make revision MSG='add table'"; exit 1; fi
	alembic revision --autogenerate -m "$(MSG)"
