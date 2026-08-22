VENV := .venv
PYTHON := $(VENV)/bin/python
MKDOCS := $(VENV)/bin/mkdocs

.PHONY: install docs-sync docs-serve docs-build check clean-site practice-package

install:
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install -r requirements.txt

docs-sync:
	$(PYTHON) scripts/sync_docs.py

docs-serve: docs-sync
	$(MKDOCS) serve

docs-build: docs-sync
	$(MKDOCS) build --strict

check: docs-sync
	$(PYTHON) scripts/check_repo.py
	git diff --check
	$(MKDOCS) build --strict --site-dir /tmp/game-dev-knowledge-mkdocs-site

clean-site:
	rm -rf site

COURSE ?= toolchain-and-git
PRACTICE_OUTPUT ?= /tmp/$(COURSE)-code.zip

practice-package:
	python3 scripts/package_practice.py --course $(COURSE) --output $(PRACTICE_OUTPUT)
