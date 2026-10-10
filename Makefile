.PHONY: help install lint format format-check test coverage check

PYTHON ?= python

help:
	@echo "Available commands:"
	@echo "  make install        Install development dependencies"
	@echo "  make lint           Run Ruff linting"
	@echo "  make format         Format Python code"
	@echo "  make format-check   Check Python formatting"
	@echo "  make test           Run the test suite"
	@echo "  make coverage       Run tests with branch coverage"
	@echo "  make check          Run lint, format-check, and coverage"

install:
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check app tests

format:
	$(PYTHON) -m ruff format app tests

format-check:
	$(PYTHON) -m ruff format --check app tests

test:
	$(PYTHON) -m pytest -v

coverage:
	$(PYTHON) -m pytest -v --cov=app --cov-branch --cov-report=term-missing

check: lint format-check coverage