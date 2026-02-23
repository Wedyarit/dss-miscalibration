.PHONY: dev seed train open setup start install

BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 3000
API_KEY ?= dev-key

dev:
	npm run dev

seed:
	curl -X POST http://localhost:$(BACKEND_PORT)/api/v1/ingest/seed \
		-H "X-API-Key: $(API_KEY)" \
		-H "Content-Type: application/json"

train:
	curl -X POST http://localhost:$(BACKEND_PORT)/api/v1/train \
		-H "X-API-Key: $(API_KEY)" \
		-H "Content-Type: application/json" \
		-d '{"confidence_threshold": 0.7, "calibration": "platt", "bins": 10}'

open:
	open http://localhost:$(FRONTEND_PORT)

setup:
	cp env.example .env

install:
	npm install
	npm install --prefix frontend
	cd backend && (test -d .venv || python3 -m venv .venv) && .venv/bin/pip install -r requirements.txt

start: setup dev
