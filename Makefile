.PHONY: backend frontend dev build start test seed

dev:
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port $${BACKEND_PORT:-8000}

frontend:
cd frontend && npm install && npm run dev

build:
cd backend && pip install poetry && poetry install --no-root && poetry build
cd frontend && npm install && npm run build

start:
docker compose up --build

seed:
cd backend && python scripts/seed_demo.py

test:
cd backend && pip install poetry && poetry install --no-root && poetry run pytest
