SHELL := /bin/zsh
APP_NAME ?= FastForm
DIST_DIR ?= dist
STAGE_DIR ?= $(DIST_DIR)/dmg_stage
SPEC ?= fastform.spec

# Extract version from pyproject.toml (fallback 0.1.0)
APP_VERSION := $(shell sed -n 's/^[[:space:]]*version[[:space:]]*=[[:space:]]*"\(.*\)"/\1/p' pyproject.toml | head -n1 || echo 0.1.0)
DMG := $(DIST_DIR)/$(APP_NAME)-$(APP_VERSION).dmg

.PHONY: setup fmt lint type test run app dmg release clean

setup:  ## Install dev deps & hooks
	pip install -e ".[dev]"
	pre-commit install || true

fmt:    ## Format & fix (ruff+black)
	ruff check --fix .
	ruff format .

lint:   ## Lint only
	ruff check .

type:   ## Type-check
	mypy src

test:   ## Run tests
	pytest -q

run:    ## Dev server
	uvicorn fastform.api.app:app --host $${FASTFORM_HOST:-127.0.0.1} --port $${FASTFORM_PORT:-8000}

app:    ## Build .app with PyInstaller
	python -m PyInstaller --clean -y $(SPEC)
	/usr/bin/codesign --force --deep -s - --timestamp=none "$(DIST_DIR)/$(APP_NAME).app" || true
	@echo "✓ $(DIST_DIR)/$(APP_NAME).app"

dmg: app ## Build versioned .dmg
	/bin/rm -rf "$(STAGE_DIR)"; mkdir -p "$(STAGE_DIR)"
	cp -R "$(DIST_DIR)/$(APP_NAME).app" "$(STAGE_DIR)/"
	ln -snf /Applications "$(STAGE_DIR)/Applications"
	hdiutil create -volname "$(APP_NAME)" -srcfolder "$(STAGE_DIR)" -ov -format UDZO "$(DMG)" >/dev/null
	@echo "✓ $(DMG)"

release: dmg ## Show artifacts
	ls -lh "$(DIST_DIR)/$(APP_NAME).app" "$(DMG)"

clean:  ## Remove build artifacts
	/bin/rm -rf build dist .pytest_cache __pycache__
