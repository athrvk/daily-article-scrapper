.PHONY: help setup install install-dev test lint format clean run

# Default target
help:
	@echo "Daily Article Scraper - Available commands:"
	@echo "  setup       - Set up the development environment"
	@echo "  install     - Install production dependencies"
	@echo "  install-dev - Install development dependencies"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting (flake8)"
	@echo "  format      - Format code (black, isort)"
	@echo "  clean       - Clean up temporary files"
	@echo "  run         - Run the scraper"
	@echo "  run-dev     - Run the scraper with debug logging"

# Setup development environment
setup:
	@echo "Setting up development environment..."
	@bash scripts/setup.sh --dev

# Install production dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
install-dev:
	pip install -r requirements-dev.txt

# Run tests
test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Run linting
lint:
	flake8 src/ config/ main.py tests/
	mypy src/ config/ main.py

# Format code
format:
	black src/ config/ main.py tests/
	isort src/ config/ main.py tests/

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf *.egg-info/

# Run the scraper
run:
	python main.py

# Run with debug logging
run-dev:
	LOG_LEVEL=DEBUG python main.py

# Create virtual environment
venv:
	python3 -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

# Check code quality
check: lint test
	@echo "Code quality check completed!"

# Build for production
build: clean format lint test
	@echo "Build completed successfully!"
