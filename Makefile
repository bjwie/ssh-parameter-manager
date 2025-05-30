.PHONY: help install install-dev clean test lint format run setup check-deps security

# Default target
help:
	@echo "SSH Parameter Manager - Development Commands"
	@echo "============================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  install      Install the package and dependencies"
	@echo "  install-dev  Install with development dependencies"
	@echo "  setup        Initial setup (create config from example)"
	@echo ""
	@echo "Development Commands:"
	@echo "  run          Start the web server"
	@echo "  test         Run tests"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code with black"
	@echo "  check-deps   Check for security vulnerabilities"
	@echo ""
	@echo "Maintenance Commands:"
	@echo "  clean        Clean up temporary files"
	@echo ""

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install black flake8 pytest pytest-cov safety

# Setup
setup:
	@if [ ! -f ssh_config.yml ]; then \
		echo "Creating ssh_config.yml from example..."; \
		cp ssh_config.example.yml ssh_config.yml; \
		echo "✅ Configuration file created. Please edit ssh_config.yml with your settings."; \
	else \
		echo "⚠️  ssh_config.yml already exists. Skipping."; \
	fi

# Development
run:
	python web_server.py

test:
	@echo "Running tests..."
	python -m pytest tests/ -v --cov=. --cov-report=html

lint:
	@echo "Running linting checks..."
	flake8 *.py --max-line-length=88 --extend-ignore=E203,W503
	@echo "✅ Linting passed"

format:
	@echo "Formatting code with black..."
	black *.py
	@echo "✅ Code formatted"

check-deps:
	@echo "Checking for security vulnerabilities..."
	safety check
	@echo "✅ Dependencies are secure"

# Maintenance
clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	@echo "✅ Cleanup complete"

# Quick development setup
dev-setup: install-dev setup
	@echo "✅ Development environment ready!"
	@echo "   1. Edit ssh_config.yml with your server details"
	@echo "   2. Run 'make run' to start the web server"
	@echo "   3. Open http://localhost:5000 in your browser"

security:
	@echo "Running security scan..."
	safety scan
	@echo "Security scan completed!" 