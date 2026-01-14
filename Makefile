# --- Config (override at call-time: `make PORT=9000 serve`) ---
PY        ?= python3
PORT      ?= 8000
ROOT      ?= .
VENV      ?= .venv
PIP       := $(VENV)/bin/pip
PYTEST    := $(PY) -m pytest

# --- Convenience URLs (used by `urls` and `smoke`) ---
BASE      := http://localhost:$(PORT)/interface-schemas
DPC_CTX   := $(BASE)/dpc/contexts/v1.jsonld
DPC_TERMS := $(BASE)/dpc/terms.ttl
DPC_SHACL := $(BASE)/dpc/shapes.ttl
DSC_CTX   := $(BASE)/dsc/contexts/v1.jsonld
DSC_TERMS := $(BASE)/dsc/terms.ttl
DSC_SHACL := $(BASE)/dsc/shapes.ttl

# --- Remote config (override at call time) ---
BASE_URL ?=
SSH_HOST ?=
WEB_ROOT ?= /var/www/livepublication

.PHONY: help init venv install serve serve-bg stop urls test smoke clean superclean
.PHONY: test-remote smoke-remote deploy-rsync build-profile check-profile test-online test-offline
.PHONY: test-crates test-policy debug-nq audit-vocab audit-vocab-offline
.PHONY: audit-sparql audit-shapes coverage-all validate-metadata

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
	@echo ""
	@echo "Remote targets (require BASE_URL):"
	@echo "  make test-remote BASE_URL=https://example.org/interface-schemas"
	@echo "  make smoke-remote BASE_URL=https://example.org/interface-schemas"
	@echo "  make deploy-rsync SSH_HOST=user@host [WEB_ROOT=/var/www/livepublication]"
	@echo "  make validate-metadata  - validate citation/metadata files"

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

validate-metadata:
	@$(PY) scripts/validate_metadata.py

# Explicitly run tests with online RO-Crate fetch
test-online:
	@ROCRATE_ONLINE=1 $(PYTEST) -q

# Force offline: use vendored RO-Crate contexts; no internet
test-offline:
	@ROCRATE_ONLINE=0 $(PYTEST) -q

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

# --- Remote validation targets ---
# Run remote pytest suite (requires BASE_URL)
test-remote: install
	@if [ -z "$(BASE_URL)" ]; then echo "Set BASE_URL, e.g. BASE_URL=https://example.org/interface-schemas"; exit 1; fi
	@BASE_URL=$(BASE_URL) $(PYTEST) -q tests/remote

# Quick header smoke check via curl (no pytest)
smoke-remote:
	@if [ -z "$(BASE_URL)" ]; then echo "Set BASE_URL, e.g. BASE_URL=https://example.org/interface-schemas"; exit 1; fi
	@echo "== HEADERS: DPC context ==" && curl -sI $(BASE_URL)/dpc/contexts/v1.jsonld | sed -n '1,12p'
	@echo "== HEADERS: DPC terms.ttl ==" && curl -sI $(BASE_URL)/dpc/terms.ttl       | sed -n '1,12p'
	@echo "== HEADERS: DPC shapes.ttl ==" && curl -sI $(BASE_URL)/dpc/shapes.ttl     | sed -n '1,12p'
	@echo "== HEADERS: DSC context ==" && curl -sI $(BASE_URL)/dsc/contexts/v1.jsonld | sed -n '1,12p'
	@echo "== HEADERS: DSC terms.ttl ==" && curl -sI $(BASE_URL)/dsc/terms.ttl         | sed -n '1,12p'
	@echo "== HEADERS: DSC shapes.ttl ==" && curl -sI $(BASE_URL)/dsc/shapes.ttl       | sed -n '1,12p'

# Optional: static rsync deploy helper (no server config here)
deploy-rsync:
	@if [ -z "$(SSH_HOST)" ]; then echo "Set SSH_HOST=user@host"; exit 1; fi
	rsync -av --delete \
		interface-schemas/ \
		$(SSH_HOST):$(WEB_ROOT)/interface-schemas/

# --- Profile context management ---
build-profile:
	@$(PY) tools/build_profile_context.py

check-profile:
	@$(PY) tools/build_profile_context.py --check

.PHONY: debug-nq
# Usage: make debug-nq FILE=tests/crates/valid/dsc_min.json
debug-nq:
	@if [ -z "$(FILE)" ]; then echo 'Usage: make debug-nq FILE=path/to.json'; exit 1; fi
	@$(PY) tools/dump_nquads.py "$(FILE)"

.PHONY: test-crates
test-crates:
	@$(PYTEST) -q tests/test_conformance_crates.py

.PHONY: test-policy
test-policy:
	@$(PYTEST) -q tests/test_policy.py

.PHONY: audit-vocab
audit-vocab: install
	@$(PYTEST) -q tests/test_vocab_audit.py::test_vocab_inventory_report
	@echo "Wrote .artifacts/vocab_inventory.json and vocab_by_file.json"

.PHONY: audit-vocab-offline
audit-vocab-offline: install
	@ROCRATE_ONLINE=0 $(PYTEST) -q tests/test_vocab_audit.py::test_vocab_inventory_report
	@echo "Wrote .artifacts/vocab_inventory.json and vocab_by_file.json (offline)"

.PHONY: audit-sparql
audit-sparql: install
	@$(PYTEST) -q tests/policy/test_vocab_sparql.py

.PHONY: audit-shapes
audit-shapes: install
	@$(PYTEST) -q tests/test_shapes_coverage.py
	@echo "Wrote .artifacts/shapes_coverage.json"

.PHONY: coverage-all
coverage-all: audit-vocab audit-sparql audit-shapes
	@echo "All diagnostic audits complete"
