# Makefile for debate system development

.PHONY: help setup validate test quality clean run-cli run-ui docker-up docker-down

# Default target
help:
	@echo "Debate System Development Commands"
	@echo "================================="
	@echo "setup        - Set up development environment"
	@echo "validate     - Validate environment setup"
	@echo "quality      - Run code quality checks"
	@echo "test         - Run tests (with dependencies)"
	@echo "clean        - Clean temporary files"
	@echo "run-cli      - Run CLI version"
	@echo "run-ui       - Run Streamlit UI"
	@echo "docker-up    - Start Docker services"
	@echo "docker-down  - Stop Docker services"

# Development setup
setup:
	@echo "🔧 Setting up development environment..."
	python dev_setup.py

# Environment validation
validate:
	@echo "🔍 Validating environment..."
	python setup_validator.py

# Code quality checks
quality:
	@echo "🔧 Running quality checks..."
	python quality_check.py

# Run tests (basic ones that don't require external deps)
test:
	@echo "🧪 Running tests..."
	python -m pytest tests/test_config_loader.py tests/test_user_feedback.py -v

# Run tests with dependencies (requires full setup)
test-full:
	@echo "🧪 Running all tests..."
	python -m pytest tests/ -v

# Clean temporary files
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true
	find . -name "tmp_*.yaml" -delete 2>/dev/null || true

# Run CLI version
run-cli:
	@echo "🚀 Starting debate system (CLI)..."
	python app/main.py

# Run Streamlit UI
run-ui:
	@echo "🚀 Starting debate system (UI)..."
	python -m streamlit run ui/streamlit_app.py

# Docker services
docker-up:
	@echo "🐳 Starting Docker services..."
	docker-compose up -d

docker-down:
	@echo "🐳 Stopping Docker services..."
	docker-compose down

# Install core dependencies
install-core:
	@echo "📦 Installing core dependencies..."
	pip install -r requirements-core.txt

# Install full dependencies  
install-full:
	@echo "📦 Installing full dependencies..."
	pip install -r requirements.txt