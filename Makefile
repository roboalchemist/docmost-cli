.PHONY: test lint format install install-dev clean help

help:
	@echo "Available targets:"
	@echo "  install      Install the package"
	@echo "  install-dev  Install with development dependencies"
	@echo "  test         Run tests"
	@echo "  lint         Run linter (ruff)"
	@echo "  format       Format code (ruff)"
	@echo "  clean        Remove build artifacts"

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

test:
	pytest -v

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
