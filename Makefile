.PHONY: help install lint format typecheck test coverage check build docs docs-serve clean update

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install:  ## Create the virtualenv and install everything
	uv sync --all-groups

lint:  ## Run ruff (lint + format check)
	uv run ruff check .
	uv run ruff format --check .

format:  ## Apply ruff autofixes and formatting
	uv run ruff check --fix .
	uv run ruff format .

typecheck:  ## Run mypy
	uv run mypy

test:  ## Run the test suite
	uv run pytest

coverage:  ## Run the test suite with a coverage report
	uv run pytest --cov --cov-report=term-missing --cov-report=xml

check: lint typecheck coverage  ## Everything CI runs

build:  ## Build the sdist and the wheel into dist/
	uv build

docs:  ## Build the documentation into site/
	uv run --group docs mkdocs build

docs-serve:  ## Serve the documentation with live reload
	uv run --group docs mkdocs serve

update:  ## Refresh uv.lock to the latest allowed versions
	uv lock --upgrade
	uv sync --all-groups

clean:  ## Remove build and cache artefacts
	rm -rf build dist site htmlcov .coverage coverage.xml
	rm -rf .mypy_cache .pytest_cache .ruff_cache
	find . -name '__pycache__' -not -path './.venv/*' -prune -exec rm -rf {} +
