dev:
	pip install -r requirements.txt
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

lint:
	python -m compileall app

test:
	python -m compileall app	

migrate:
	alembic upgrade head

revision:
	@if [ -z "$(MSG)" ]; then echo "MSG is required, e.g. make revision MSG='add table'"; exit 1; fi
	alembic revision --autogenerate -m "$(MSG)"
