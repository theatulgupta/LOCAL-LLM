.PHONY: help install dev prod test lint format clean typecheck

help:
	@echo "Local LLM Server - Makefile Commands"
	@echo "===================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Install dependencies with uv"
	@echo "  make dev          - Start development server with hot reload"
	@echo "  make prod         - Start production server"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make lint         - Run code linter"
	@echo "  make format       - Format code with black"
	@echo "  make typecheck    - Run type checking with mypy"
	@echo ""
	@echo "Cleaning:"
	@echo "  make clean        - Remove cache and build files"

install:
	uv sync

dev:
	bash dev.sh

prod:
	bash start.sh

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=app --cov-report=html --cov-report=term

lint:
	flake8 app/ tests/
	pylint app/

format:
	black app/ tests/
	isort app/ tests/

typecheck:
	mypy app/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov dist build *.egg-info
	rm -rf .mypy_cache

all: clean install test
