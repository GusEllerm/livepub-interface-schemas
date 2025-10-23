# --- Config (override at call-time: `make PORT=9000 serve`) ---
PY        ?= python3
PORT      ?= 8000
ROOT      ?= .
VENV      ?= .venv
PIP       := $(VENV)/bin/pip
PYTEST    := $(VENV)/bin/pytest

# --- Convenience URLs (used by `urls` and `smoke`) ---
BASE      := http://localhost:$(PORT)/interface-schemas
DPC_CTX   := $(BASE)/dpc/contexts/v1.jsonld
DPC_TERMS := $(BASE)/dpc/terms.ttl
DPC_SHACL := $(BASE)/dpc/shapes.ttl
DSC_CTX   := $(BASE)/dsc/contexts/v1.jsonld
DSC_TERMS := $(BASE)/dsc/terms.ttl
DSC_SHACL := $(BASE)/dsc/shapes.ttl

.PHONY: help init venv install serve serve-bg stop urls test smoke clean superclean

help:
	@echo "Targets:"
	@echo "  make init        - create venv + install dev deps"
	@echo "  make serve       - run local dev server (fg) on PORT=$(PORT)"
	@echo "  make serve-bg    - run dev server in background; write PID to .server.pid"
	@echo "  make stop        - stop background server (if running)"
	@echo "  make urls        - print local URLs for quick manual checks"
	@echo "  make test        - run full pytest suite (auto-spawns its own server)"
	@echo "  make smoke       - start server, curl key endpoints, stop server"
	@echo "  make clean       - remove caches"
	@echo "  make superclean  - clean + remove venv"

# --- Setup ---
init: venv install

venv:
	@$(PY) -m venv $(VENV)

install: venv
	@$(PIP) install -r requirements-dev.txt

# --- Dev server ---
serve:
	@./serve_dev.py --root $(ROOT) --port $(PORT)

serve-bg:
	@./serve_dev.py --root $(ROOT) --port $(PORT) >/dev/null 2>&1 & echo $$! > .server.pid
	@echo "Server running at http://localhost:$(PORT) (PID $$(cat .server.pid))"

stop:
	@if [ -f .server.pid ]; then kill -TERM `cat .server.pid` && rm .server.pid && echo "Server stopped."; \
	else echo "No .server.pid found; is the server running?"; fi

urls:
	@echo "DPC context:    $(DPC_CTX)"
	@echo "DPC terms.ttl:  $(DPC_TERMS)"
	@echo "DPC shapes.ttl: $(DPC_SHACL)"
	@echo "DSC context:    $(DSC_CTX)"
	@echo "DSC terms.ttl:  $(DSC_TERMS)"
	@echo "DSC shapes.ttl: $(DSC_SHACL)"

# --- Tests ---
test: install
	@$(PYTEST) -q

# quick manual header smoke test (requires curl)
smoke: install serve-bg
	@echo "== HEADERS: DPC v1 context ==" && curl -sI $(DPC_CTX)   | sed -n '1,12p'
	@echo "== HEADERS: DPC terms.ttl   ==" && curl -sI $(DPC_TERMS) | sed -n '1,12p'
	@echo "== HEADERS: DPC shapes.ttl  ==" && curl -sI $(DPC_SHACL) | sed -n '1,12p'
	@echo "== HEADERS: DSC v1 context ==" && curl -sI $(DSC_CTX)   | sed -n '1,12p'
	@echo "== HEADERS: DSC terms.ttl   ==" && curl -sI $(DSC_TERMS) | sed -n '1,12p'
	@echo "== HEADERS: DSC shapes.ttl  ==" && curl -sI $(DSC_SHACL) | sed -n '1,12p'
	@$(MAKE) -s stop

# --- Cleanup ---
clean:
	@find . -name "__pycache__" -type d -prune -exec rm -rf {} + || true
	@find . -name "*.pyc" -delete || true

superclean: clean
	@rm -rf $(VENV)
	@rm -f .server.pid
