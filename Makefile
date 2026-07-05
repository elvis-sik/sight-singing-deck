SHELL := /bin/bash
.DEFAULT_GOAL := help

PYTHON ?= python3
UV ?= uv
WORKBENCH ?= anki-workbench
DOCKER_IMAGE ?= sight-singing-deck-anki-workbench
WORKBENCH_DOCKERFILE ?= .tmp/anki-workbench/Dockerfile

PY_FILES := $(shell git ls-files --cached --others --exclude-standard '*.py' ':!:out/**' ':!:dist/**' ':!:node_modules/**' ':!:.venv/**' ':!:input/**' ':!:media/**' ':!:backups/**' ':!:templates/**' ':!:drafts/**' ':!:_vendor/**')
MYPY_FILES := $(shell git ls-files --cached --others --exclude-standard '*.py' ':!:tests/**' ':!:out/**' ':!:dist/**' ':!:node_modules/**' ':!:.venv/**' ':!:input/**' ':!:media/**' ':!:backups/**' ':!:templates/**' ':!:drafts/**' ':!:_vendor/**')
JS_FILES := $(shell git ls-files --cached --others --exclude-standard '*.js' '*.mjs' ':!:out/**' ':!:dist/**' ':!:node_modules/**')
SHELL_FILES := $(shell git ls-files --cached --others --exclude-standard '*.sh')

.PHONY: help lint lint-paths lint-python lint-js lint-shell type test apkg workbench-dockerfile workbench-smoke check

help:
	@printf "Available targets:\n"
	@printf "  make lint   Run linters and source hygiene checks\n"
	@printf "  make type   Run type checks where typed source exists\n"
	@printf "  make test   Run unit tests and repository hygiene tests\n"
	@printf "  make apkg   Build the sight-singing APKGs\n"
	@printf "  make workbench-smoke  Build APKGs and run disposable Anki smoke\n"
	@printf "  make check  Run lint, type, and test\n"

lint: lint-paths lint-python lint-js lint-shell

lint-paths:
	@$(PYTHON) tests/test_repo_hygiene.py --path-only

lint-python:
	@if [ -n "$(PY_FILES)" ]; then \
		if [ -f pyproject.toml ]; then \
			$(UV) run --extra dev ruff check $(PY_FILES); \
		else \
			$(PYTHON) -m compileall -q $(PY_FILES); \
		fi; \
	else \
		printf "No Python files to lint.\n"; \
	fi

lint-js:
	@if [ -n "$(JS_FILES)" ]; then \
		for file in $(JS_FILES); do node --check "$$file"; done; \
	else \
		printf "No JavaScript files to lint.\n"; \
	fi

lint-shell:
	@if [ -n "$(SHELL_FILES)" ]; then \
		for file in $(SHELL_FILES); do bash -n "$$file"; done; \
	else \
		printf "No shell files to lint.\n"; \
	fi

type:
	@if [ -n "$(MYPY_FILES)" ]; then \
		if [ -f pyproject.toml ]; then \
			$(UV) run --extra dev mypy $(MYPY_FILES); \
		else \
			$(PYTHON) -m compileall -q $(MYPY_FILES); \
		fi; \
	else \
		printf "No Python files to type-check.\n"; \
	fi
	@if [ -f package.json ] && node -e "const p=require('./package.json'); process.exit(p.scripts && p.scripts.typecheck ? 0 : 1)"; then \
		npm run typecheck; \
	elif [ -f package.json ]; then \
		printf "No npm typecheck script configured.\n"; \
	fi

test:
	@if [ -d tests ]; then $(PYTHON) -m unittest discover -s tests -v; fi
	@if [ -f package.json ] && node -e "const p=require('./package.json'); process.exit(p.scripts && p.scripts.test ? 0 : 1)"; then \
		npm test; \
	fi

apkg:
	$(UV) run --extra deck python scripts/build_deck.py
	$(UV) run --extra deck python scripts/build_transcription_debug_deck.py
	$(UV) run --extra deck python scripts/build_transcription_integration_debug_deck.py
	$(UV) run --extra deck python scripts/build_notetype_smoke_deck.py

workbench-dockerfile:
	$(WORKBENCH) dockerfile --out $(WORKBENCH_DOCKERFILE)

workbench-smoke: apkg workbench-dockerfile
	docker build -f $(WORKBENCH_DOCKERFILE) -t $(DOCKER_IMAGE) .
	docker run --rm --mount type=bind,source="$(CURDIR)",target=/workspace -w /workspace $(DOCKER_IMAGE)

# Real-input pointer probe: drives the reviewer's transcription editor with
# xdotool inside Docker/Xvfb and checks the placed pitch matches the aim.
# Override SS_PROBE_ZOOM (e.g. 2.0) to test a scaled webview.
SS_PROBE_ZOOM ?= 1
workbench-pointer-smoke:
	docker run --rm \
		-e SS_PROBE_ZOOM=$(SS_PROBE_ZOOM) \
		-e SS_PROBE_SHOT_DIR=/workspace/out \
		--mount type=bind,source="$(CURDIR)",target=/workspace -w /workspace \
		$(DOCKER_IMAGE) \
		sh -lc 'Xvfb :99 -screen 0 1280x1024x24 -nolisten tcp & xvfb_pid=$$!; export DISPLAY=:99; python3 -m anki_addon_workbench --config-root tests/gui_smoke/pointer smoke; status=$$?; kill "$$xvfb_pid" 2>/dev/null || true; exit "$$status"'

check: lint type test
