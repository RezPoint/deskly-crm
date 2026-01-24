dev:
	pip install -r requirements.txt
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

lint:
	python -m compileall app

test:
	python -m compileall app	