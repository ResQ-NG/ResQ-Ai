.PHONY: help install setup dev run test lint format clean docker-build docker-up docker-down env-setup check-env

# Default target when just running 'make'
help: ## Show this help message
	@echo "ResQ AI - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# Setup and Installation
install: ## Install Python dependencies
	pip install -r requirements.txt

setup: ## Complete setup - create venv and install dependencies
	python3 -m venv venv
	@echo "Virtual environment created. Activate it with: source venv/bin/activate"
	@echo "Then run: make install"

env-setup: ## Create .env file from example
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "✅ Created .env file. Please edit it with your credentials."; \
	else \
		echo "⚠️  .env file already exists. Skipping..."; \
	fi

check-env: ## Verify .env file exists and has required variables
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found! Run 'make env-setup' first."; \
		exit 1; \
	else \
		echo "✅ .env file found"; \
		grep -q "AWS_ACCESS_KEY_ID=your_aws_access_key_id_here" .env && \
		echo "⚠️  Warning: Using default AWS credentials. Update your .env file!" || \
		echo "✅ AWS credentials configured"; \
	fi

# Development
dev: check-env ## Run development server with auto-reload
	@if [ -f venv/bin/uvicorn ]; then \
		HOST=$$(grep '^HOST=' .env | cut -d'=' -f2- | xargs) ; \
		PORT=$$(grep '^PORT=' .env | cut -d'=' -f2- | xargs) ; \
		HOST_ARG=$${HOST:-0.0.0.0} ; \
		PORT_ARG=$${PORT:-8000} ; \
		./venv/bin/uvicorn app.main:app --reload --host $${HOST_ARG} --port $${PORT_ARG}; \
	else \
		echo "❌ Virtual environment not found or uvicorn not installed."; \
		echo "Run: source venv/bin/activate && pip install -r requirements.txt"; \
		exit 1; \
	fi

run: check-env ## Run production server
	@if [ -f venv/bin/python ]; then \
		./venv/bin/python -m app.main; \
	else \
		echo "❌ Virtual environment not found."; \
		echo "Run: make setup && source venv/bin/activate && make install"; \
		exit 1; \
	fi

# Code Quality
lint: ## Run pylint on the codebase
	pylint app/

format: ## Format code with black
	black app/

format-check: ## Check code formatting without making changes
	black --check app/

# Testing
test: ## Run tests (placeholder for when you add tests)
	@echo "No tests configured yet. Add pytest to requirements.txt and create tests/"
	# pytest tests/ -v

test-coverage: ## Run tests with coverage report
	@echo "No tests configured yet."
	# pytest tests/ --cov=app --cov-report=html

# Docker Commands
docker-build: ## Build Docker image
	docker build -t resq-ai:latest .

docker-up: ## Start application with Docker Compose
	docker-compose -f deployment/docker-compose.yml up -d

docker-down: ## Stop Docker Compose services
	docker-compose -f deployment/docker-compose.yml down

docker-dev: ## Start development environment with Docker Compose
	docker-compose -f deployment/docker-compose.dev.yml up

docker-logs: ## View Docker container logs
	docker-compose -f deployment/docker-compose.yml logs -f

docker-restart: ## Restart Docker services
	docker-compose -f deployment/docker-compose.yml restart

# Cleanup
clean: ## Remove Python cache files and temporary files
	find ./app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find ./app -type f -name "*.pyc" -delete 2>/dev/null || true
	find ./app -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -maxdepth 2 -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -maxdepth 2 -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -maxdepth 2 -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	find . -maxdepth 2 -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned up cache files and temporary files"

clean-all: clean ## Remove cache files and virtual environment
	rm -rf venv/
	@echo "✅ Removed virtual environment"

# Dependency Management
freeze: ## Update requirements.txt with current dependencies
	pip freeze > requirements.txt
	@echo "✅ Updated requirements.txt"

upgrade: ## Upgrade all dependencies
	pip install --upgrade pip
	pip list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip install -U
	@echo "✅ All packages upgraded. Run 'make freeze' to update requirements.txt"

# Quick Start
quick-start: env-setup install ## Quick setup for new developers
	@echo ""
	@echo "✅ Quick start complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Edit .env file with your AWS credentials"
	@echo "  2. Activate virtual environment: source venv/bin/activate"
	@echo "  3. Run the server: make dev"
	@echo ""

# Health Check
health: ## Check if the server is running
	@curl -s http://localhost:8000/ | grep -q "Hello World" && \
		echo "✅ Server is running!" || \
		echo "❌ Server is not responding"

# Database (placeholder for future use)
db-migrate: ## Run database migrations (placeholder)
	@echo "Database migrations not configured yet"
	# alembic upgrade head

db-rollback: ## Rollback last database migration (placeholder)
	@echo "Database migrations not configured yet"
	# alembic downgrade -1

# Info
info: ## Show project information
	@echo "ResQ AI - Project Information"
	@echo "================================"
	@echo "Python Version: $$(python --version 2>&1)"
	@echo "Pip Version: $$(pip --version 2>&1 | cut -d' ' -f1,2)"
	@echo "Virtual Env: $${VIRTUAL_ENV:-Not activated}"
	@echo "Project Path: $$(pwd)"
	@echo ""
	@if [ -f .env ]; then \
		echo "✅ .env file exists"; \
	else \
		echo "❌ .env file missing"; \
	fi
	@echo ""
