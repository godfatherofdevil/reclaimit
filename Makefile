.PHONY: venv install test lint check doctor package-deb package-rpm

venv:
	python3.12 -m venv .venv

install:
	.venv/bin/pip install -e ".[dev,tui]"

test:
	.venv/bin/python -m pytest

lint:
	.venv/bin/python -m ruff check src tests

check: test lint

doctor:
	.venv/bin/reclaimit doctor

package-deb:
	packaging/scripts/build-deb.sh

package-rpm:
	packaging/scripts/build-rpm.sh
