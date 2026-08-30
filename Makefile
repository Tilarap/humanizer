VENV ?= .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff

.PHONY: setup run lint test test-fast

setup: $(PYTHON)
	$(PIP) install -r requirements-dev.txt

$(PYTHON):
	python3.12 -m venv $(VENV)

run:
	$(PYTHON) -m app.main

lint:
	$(RUFF) check .
	$(RUFF) format --check .

test: test-fast

test-fast:
	$(PYTEST) -m "not live and not eval" --cov=app --cov-report=term-missing
