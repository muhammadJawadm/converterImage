# Quick Start Scripts for File Converter

# Start all services with Docker
start-docker:
	docker-compose up --build

# Start services in background
start-docker-bg:
	docker-compose up -d --build

# Stop all services
stop-docker:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Worker logs only
logs-worker:
	docker-compose logs -f celery-worker

# Scale workers (e.g., make scale-workers N=5)
scale-workers:
	docker-compose up --scale celery-worker=$(N)

# Restart services
restart:
	docker-compose restart

# Clean up everything
clean:
	docker-compose down -v --rmi all

# Local development - Start Redis
start-redis:
	docker run -d -p 6379:6379 --name file-converter-redis redis:7-alpine

# Local development - Start Celery worker (Windows)
start-worker-windows:
	celery -A app.celery_app worker --loglevel=info --pool=solo

# Local development - Start Celery worker (Linux/Mac)
start-worker:
	celery -A app.celery_app worker --loglevel=info

# Local development - Start Flower
start-flower:
	celery -A app.celery_app flower

# Local development - Start FastAPI
start-api:
	python -m uvicorn app.main:app --reload

# Check health
health:
	curl http://localhost:8000/health

# Install dependencies
install:
	pip install -r requirements.txt

# Test API documentation
test-docs:
	start http://localhost:8000/docs

# Open Flower dashboard
flower:
	start http://localhost:5555

.PHONY: start-docker start-docker-bg stop-docker logs logs-worker scale-workers restart clean start-redis start-worker-windows start-worker start-flower start-api health install test-docs flower
