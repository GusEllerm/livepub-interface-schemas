# LivePublication Interface Schemas (local dev)

This project provides **local development and validation** for the DPC (Distributed Provenance Crate) and DSC (Distributed Step Crate) vocabularies, JSON-LD contexts, SHACL shapes, and HTML landing pages.

## Quick start

```bash
make init    # Create venv + install deps
make test    # Run full validation suite (all tests)
make serve   # Start dev server (foreground)
```

## Project structure

```
interface-schemas/
├── dpc/
│   ├── index.html           # DPC landing page
│   ├── terms.ttl            # DPC vocabulary (Turtle)
│   ├── shapes.ttl           # DPC SHACL shapes
│   └── contexts/
│       └── v1.jsonld        # DPC JSON-LD context v1 (immutable)
├── dsc/
│   ├── index.html           # DSC landing page
│   ├── terms.ttl            # DSC vocabulary (Turtle)
│   ├── shapes.ttl           # DSC SHACL shapes
│   └── contexts/
│       └── v1.jsonld        # DSC JSON-LD context v1 (immutable)
└── index.html               # Catalog page
tests/
├── conftest.py              # Pytest fixture (auto-starts server)
├── test_headers.py          # MIME, CORS, Cache-Control checks
├── test_jsonld_roundtrip.py # JSON-LD expand/compact validation
├── test_turtle_parses.py    # TTL parsing + ontology sanity checks
├── test_shacl.py            # SHACL validation
└── test_html_links.py       # Link resolution checks
```

## Run dev server

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
./serve_dev.py --root . --port 8000
```

Visit:
- http://localhost:8000/interface-schemas/dpc/contexts/v1.jsonld
- http://localhost:8000/interface-schemas/dpc/terms.ttl
- http://localhost:8000/interface-schemas/dpc/shapes.ttl

## Run full validation suite (pytest)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

The test suite validates:
- ✅ HTTP 200s for all artifacts
- ✅ Correct MIME types (`application/ld+json`, `text/turtle`, `text/html`)
- ✅ CORS headers (`Access-Control-Allow-Origin: *`)
- ✅ Strong caching for versioned contexts (`Cache-Control: public, max-age=31536000, immutable`)
- ✅ JSON-LD expansion and compaction semantics
- ✅ Turtle parsing and ontology structure
- ✅ SHACL validation against sample data
- ✅ HTML link resolution (no broken links)

## Makefile shortcuts

- **One-time setup**: `make init`
- **Run server (fg)**: `make serve` (Ctrl-C to stop)
- **Run server (bg)**: `make serve-bg` (PID saved to `.server.pid`)
- **Stop server**: `make stop`
- **Print URLs**: `make urls`
- **Full test suite**: `make test` (auto-spawns server)
- **Header smoke test**: `make smoke` (starts+stops server, curls endpoints)
- **Cleanup**: `make clean` or `make superclean`

## Workflow: Updating vocabularies, contexts, or shapes

### When to update

- **Terms (vocabulary)**: Add/modify classes or properties in `terms.ttl`
- **Contexts (JSON-LD)**: Add new term mappings or change typing rules in `contexts/vX.jsonld`
- **Shapes (SHACL)**: Add/modify validation constraints in `shapes.ttl`

### Workflow

1. **Edit the artifact**
   ```bash
   # Example: Add a new class to DPC
   vim interface-schemas/dpc/terms.ttl
   ```

2. **Update test data** (if applicable)
   ```bash
   # If you added a new property, update test fixtures
   vim tests/data_dpc.ttl
   vim tests/sample_dpc.json
   ```

3. **Run validation**
   ```bash
   make test
   ```
   
   If tests fail:
   - Check TTL syntax: `make serve` then visit the `.ttl` file
   - Check JSON-LD: `python -m json.tool interface-schemas/dpc/contexts/v1.jsonld`
   - Review test output for specific assertion failures

4. **Update SHACL shapes** (if vocabulary changed)
   ```bash
   vim interface-schemas/dpc/shapes.ttl
   # Add constraints for new properties/classes
   make test  # Re-validate
   ```

5. **Version contexts** (for breaking changes only)
   
   **Important**: Existing versioned contexts (e.g., `v1.jsonld`) are **immutable** once published. If you must make a breaking change:
   
   ```bash
   # Create a new version
   cp interface-schemas/dpc/contexts/v1.jsonld interface-schemas/dpc/contexts/v2.jsonld
   vim interface-schemas/dpc/contexts/v2.jsonld  # Make changes
   
   # Update index.html to reference v2
   vim interface-schemas/dpc/index.html
   
   # Update tests to use v2 (or add parallel tests)
   vim tests/test_jsonld_roundtrip.py
   
   make test  # Validate
   ```

6. **Commit changes**
   ```bash
   git add interface-schemas/ tests/
   git commit -m "feat(dpc): add NewClass and newProperty to vocabulary"
   ```

### Context versioning policy

- **v1, v2, etc.** are **immutable** after first publication
- Non-breaking additions (new terms) can go into the existing version
- Breaking changes (removing terms, changing `@type` semantics) **require a new version**
- Serve all versions indefinitely with strong caching

### Testing checklist

After editing vocabularies/contexts/shapes:

```bash
make test                      # Full suite (15 tests)
make serve                     # Manual inspection
curl -I http://localhost:8000/interface-schemas/dpc/contexts/v1.jsonld  # Check headers
```

Expected: All tests green, no broken links, correct MIME types.

## Remote validation (staging/prod)

Set `BASE_URL` to your deployed base (e.g., `https://livepublication.org/interface-schemas`) and run:

```bash
# Quick header checks (no pytest)
make smoke-remote BASE_URL=https://livepublication.org/interface-schemas

# Full remote test suite (pytest)
make test-remote BASE_URL=https://livepublication.org/interface-schemas
```

**Notes:**
- Remote tests are **skipped** unless `BASE_URL` is set
- Remote JSON-LD tests perform live expansion/compaction against the deployed context URL
- Versioned contexts (e.g., `.../v1.jsonld`) must return `Cache-Control: public, max-age=31536000, immutable`
- Remote tests validate headers, CORS, JSON-LD semantics, and link integrity

**Optional: Deploy helper**

```bash
# Deploy via rsync (adjust SSH_HOST and WEB_ROOT)
make deploy-rsync SSH_HOST=user@host WEB_ROOT=/var/www/livepublication
```

This copies `interface-schemas/` to the remote server. **No web server configuration is modified.**

Expected: All tests green, no broken links, correct MIME types.

## Commit

```bash
git add .
git -c user.name="REPLACE_WITH_YOUR_NAME" -c user.email="devnull@example.com" commit -m "feat: local skeleton for DPC/DSC with contexts, TTL, SHACL, dev server, tests"
```
