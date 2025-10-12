.PHONY: dev seed train open clean logs

# Development commands
dev:
	docker-compose up -d
	@echo "Services started. Backend: http://localhost:$${BACKEND_PORT:-8000}, Frontend: http://localhost:$${FRONTEND_PORT:-3000}"

seed:
	@echo "Seeding database with demo data..."
	curl -X POST http://localhost:$${BACKEND_PORT:-8000}/api/v1/ingest/seed \
		-H "X-API-Key: $$(grep API_KEY env.example | cut -d'=' -f2)" \
		-H "Content-Type: application/json"

train:
	@echo "Training model..."
	curl -X POST http://localhost:$${BACKEND_PORT:-8000}/api/v1/train \
		-H "X-API-Key: $$(grep API_KEY env.example | cut -d'=' -f2)" \
		-H "Content-Type: application/json" \
		-d '{"confidence_threshold": 0.7, "calibration": "platt", "bins": 10}'

open:
	@echo "Opening frontend..."
	open http://localhost:$${FRONTEND_PORT:-3000}

# Utility commands
clean:
	docker-compose down -v
	docker system prune -f

logs:
	docker-compose logs -f

# Setup commands
setup:
	@echo "Setting up environment..."
	cp env.example .env
	@echo "Environment file created. Edit .env as needed."

# Quick start
start: setup dev
	@echo "Waiting for services to start..."
	sleep 10
	@echo "Seeding database..."
	$(MAKE) seed
	@echo "Training model..."
	$(MAKE) train
	@echo "Setup complete! Open http://localhost:3000"
