.PHONY: test test-unit test-integration lint format install install-dev clean help

help:
	@echo "Available targets:"
	@echo "  install           Install the package"
	@echo "  install-dev       Install with development dependencies"
	@echo "  test              Run all tests (unit + integration)"
	@echo "  test-unit         Run unit tests only"
	@echo "  test-integration  Run integration tests (requires live server)"
	@echo "  lint              Run linter (ruff)"
	@echo "  format            Format code (ruff)"
	@echo "  clean             Remove build artifacts"

install:
	uv pip install --system -e .

install-dev:
	uv pip install --system -e ".[dev]"

test:
	pytest -v

test-unit:
	pytest -v --ignore=tests/test_integration.py

test-integration:
	pytest -v tests/test_integration.py

lint:
	ruff check src/

format:
	ruff check --fix src/
	ruff format src/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
