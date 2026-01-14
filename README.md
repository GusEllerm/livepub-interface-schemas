# LivePublication Interface Schemas

## What this repository is
This repository contains the LivePublication interface schemas used to describe distributed provenance-aware workflow executions. It provides the DPC (Distributed Provenance Crate) and DSC (Distributed Step Crate) vocabularies plus supporting artifacts for validation and publishing. These schemas are used in Chapter 5 (Distributed provenance-aware WMS). 

## What's included
- DPC vocabulary (Turtle), SHACL shapes, JSON-LD context, and landing page
- DSC vocabulary (Turtle), SHACL shapes, JSON-LD context, and landing page
- Profile context `lp-dscdpc` that merges DPC + DSC for RO-Crate use
- Schema catalog page for interface-schemas
- Example crates and validation tests
- Vendored RO-Crate contexts for offline tests

## Where the published schemas live
- https://w3id.org/livepublication/interface-schemas/
- https://w3id.org/livepublication/interface-schemas/dpc/
- https://w3id.org/livepublication/interface-schemas/dsc/
- https://w3id.org/livepublication/interface-schemas/contexts/lp-dscdpc/v1.jsonld

## How to cite
Cite this repository as: "LivePublication Interface Schemas". DOI: (to be assigned after Zenodo release). The Zenodo DOI will be minted on release and should replace the placeholder in metadata files.

## License
CC BY 4.0 (see `LICENSE`).

## Metadata validation
Run `python scripts/validate_metadata.py` (or `make validate-metadata`) to check required metadata files, JSON/YAML parsing, and cross-file consistency.

## RO-Crate regeneration
Run `python scripts/generate_ro_crate.py` to regenerate `ro-crate-metadata.json`.

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
│   ├── index.html                # DPC landing page
│   ├── terms.ttl                 # DPC vocabulary (Turtle)
│   ├── shapes.ttl                # DPC SHACL shapes
│   └── contexts/
│       └── v1.jsonld             # DPC JSON-LD context v1 (immutable)
├── dsc/
│   ├── index.html                # DSC landing page
│   ├── terms.ttl                 # DSC vocabulary (Turtle)
│   ├── shapes.ttl                # DSC SHACL shapes
│   └── contexts/
│       └── v1.jsonld             # DSC JSON-LD context v1 (immutable)
├── contexts/
│   └── lp-dscdpc/
│       └── v1.jsonld             # Profile context (merged DPC+DSC)
├── vendor/                       # Vendored contexts for offline tests
│   ├── ro-crate/1.1/context.jsonld
│   └── ro-terms/workflow-run/context.jsonld
├── index.html                    # Catalog page
└── ...

tests/
├── crates/
│   ├── valid/                    # Example crates that MUST conform
│   └── invalid/                  # Example crates that MUST violate
├── _example_loader.py            # Centralized example discovery
└── _jsonld_utils.py              # Expansion and loader helpers

tools/
├── build_profile_context.py      # Generate merged profile context
└── dump_nquads.py                # Debug helper: JSON-LD → N-Quads

Makefile                          # Dev, test, and helper targets
serve_dev.py                      # Minimal static server for local dev
requirements-dev.txt              # Dev/test dependencies
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

## Run validation suite (pytest)

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
   vim tests/test_json/dpc_min.json
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

## Example crates: structure & conventions

All JSON/JSON-LD examples live under:

```
tests/crates/
   valid/    # MUST conform to SHACL
   invalid/  # MUST violate (ideally one focused violation per file)
```

### Requirements for valid crates

- Contexts: include RO-Crate and the profile.

  - Always: `https://w3id.org/ro/crate/1.1/context`
  - Always: `https://livepublication.org/interface-schemas/contexts/lp-dscdpc/v1.jsonld`
  - Optional when applicable: `https://w3id.org/ro/terms/workflow-run/context`

  Example:

  ```json
  {
     "@context": [
        "https://w3id.org/ro/crate/1.1/context",
        "https://w3id.org/ro/terms/workflow-run/context",
        "https://livepublication.org/interface-schemas/contexts/lp-dscdpc/v1.jsonld"
     ]
  }
  ```
- DistributedStep I/O (normative): use Schema.org

  - `object` (input) and/or `result` (output) — at least one is required.
  - `prov:used`/`prov:generated` are optional/legacy and do not satisfy conformance by themselves.
- Runtime linking: `schema:hasPart` points to a `dpc:HardwareRuntime` with ≥1 `dpc:component`.
- Hardware metrics: use `schema:additionalProperty` with `schema:PropertyValue { name, value }`.
- HowToStep: `schema:position` is an integer; `schema:identifier` optional (string).
- HTTPS only: profile ensures `https://schema.org/...`; tests fail if `http://schema.org/...` appears.

### Requirements for invalid crates

Put targeted counter-examples in `tests/crates/invalid/`, each demonstrating one clear violation (e.g., missing `object/result`, wrong datatype for `position`, `HardwareRuntime` without `component`, raw hardware keys instead of `additionalProperty`, etc.).

### Running tests

Local (RO-Crate contexts fetched online by default):

```bash
make test          # full suite
make test-crates   # conformance only
make test-policy   # profile/targets checks
```

Offline (vendored RO-Crate contexts):

```bash
make test-offline
```

Remote/staging validation (after deploy):

```bash
make test-remote BASE_URL=https://livepublication.org/interface-schemas
```

Debugging expansion:

```bash
make debug-nq FILE=tests/crates/valid/dsc_min.json
```

Vocabulary audit (see what terms/namespaces are actually used):

```bash
make audit-vocab         # online (fetches RO-Crate contexts)
make audit-vocab-offline # offline (vendored contexts)
```

The audit produces a JSON report at `.artifacts/vocab_inventory.json` with:

- Predicate and class counts by namespace
- Top terms used across all crates
- Literal datatype distribution (XSD types)
- Any `http://schema.org/*` predicates (should be zero for valid crates)
- Unknown namespaces not in the allowlist

The audit also runs a contract test on valid crates to ensure:

- No `http://schema.org/*` predicates (HTTPS only)
- Native XSD types present for booleans/numbers

> The suite enforces no examples under `tests/test_json/` (a guard test will fail if any remain).

## Vocabulary audit

The vocabulary audit system inventories and validates term usage across all crates, answering: *"What vocabularies and terms are actually used, and are they aligned with policy?"*

### Running the audit

```bash
make audit-vocab         # online (fetches RO-Crate contexts)
make audit-vocab-offline # offline (vendored contexts)
```

### What it produces

A JSON report at `.artifacts/vocab_inventory.json` containing:

- **by_namespace**: Predicate counts per namespace (e.g., 1,423 Schema.org predicates, 31 DPC, 14 DC Terms)
- **by_term**: Top 100 terms by usage (e.g., `schema:name`: 439, `schema:value`: 338, `schema:additionalProperty`: 330)
- **classes_by_namespace**: Class counts by namespace
- **literal_types**: Literal datatype distribution (e.g., 18 `xsd:integer`, 17 `xsd:double`, 6 `xsd:boolean`)
- **http_schema_terms**: Any `http://schema.org/*` predicates found (should be empty for valid crates)
- **unknown_namespaces**: Namespaces not in the allowlist (should be empty)

### Contract checks (enforced on valid crates)

The audit includes a contract test (`test_valid_crates_vocab_contract`) that **fails** if:

1. Any `http://schema.org/*` predicates are found (must use HTTPS)
2. No native XSD types are present for booleans/numbers

### Current inventory snapshot

Based on the latest audit of `tests/crates/{valid,invalid}`:

**Top 5 namespaces:**

1. `https://schema.org/`: 1,423 predicates 
2. `http://www.w3.org/1999/02/22-rdf-syntax-ns#`: 507 (rdf:type)
3. `https://livepublication.org/interface-schemas/dpc#`: 31
4. `http://purl.org/dc/terms/`: 14 (conformsTo)
5. `https://w3id.org/ro/terms/workflow-run#`: 12

**Top 10 terms:**

1. `rdf:type`: 507
2. `schema:name`: 439
3. `schema:value`: 338
4. `schema:additionalProperty`: 330
5. `schema:hasPart`: 53
6. `schema:encodingFormat`: 29
7. `schema:description`: 28
8. `dpc:component`: 24
9. `schema:object`: 15
10. `dcterms:conformsTo`: 14

**Literal types (native XSD):**

- `xsd:integer`: 18
- `xsd:double`: 17
- `xsd:boolean`: 6
- `xsd:date`: 6
- `xsd:dateTime`: 2

**Contract status:**

- ✅ Zero `http://schema.org/*` predicates
- ✅ Native XSD types present
- ✅ All namespaces recognized

### Allowed namespaces

The audit allows predicates from these namespaces:

- `https://schema.org/` (must be HTTPS)
- `http://www.w3.org/ns/prov#` (W3C PROV is HTTP)
- `http://www.w3.org/1999/02/22-rdf-syntax-ns#` (RDF)
- `http://www.w3.org/2000/01/rdf-schema#` (RDFS)
- `http://www.w3.org/2001/XMLSchema#` (XSD datatypes)
- `https://w3id.org/ro/crate/1.1/` (RO-Crate)
- `https://w3id.org/ro/terms/workflow-run#` (Workflow-run)
- `https://livepublication.org/interface-schemas/dpc#` (DPC vocabulary)
- `https://livepublication.org/interface-schemas/dsc#` (DSC vocabulary)
- `http://purl.org/dc/terms/` (Dublin Core Terms)
- `https://bioschemas.org/` (Bioschemas)

Any other namespace triggers a warning in the report.

### HTTPS enforcement

The profile context (`lp-dscdpc/v1.jsonld`) explicitly overrides 23+ RO-Crate terms to force HTTPS Schema.org IRIs:

```
about, actionStatus, additionalType, agent, alternateName, applicationCategory,
contentSize, datePublished, email, encodingFormat, endTime, exampleOfWork,
familyName, givenName, instrument, license, mainEntity, programmingLanguage,
startTime, url, version, workExample, etc.
```

This ensures consistency: even when RO-Crate contexts expand terms to `http://schema.org/*`, our profile re-maps them to `https://schema.org/*`.

## JSON-LD → RDF pipeline

Examples are expanded with `pyld` using a custom document loader (rewrites our contexts to the local dev server or `BASE_URL`, and allowlists RO-Crate contexts). We then convert to N-Quads with:

- `format = application/n-quads`
- `useNativeTypes = true` (JSON numbers/booleans map to XSD typed literals)
- `produceGeneralizedRdf = false`

N-Quads are parsed into an `rdflib.Graph` for SHACL validation. If examples ever start producing named graphs, `tests/test_named_graph_tripwire.py` will fail so we can revisit flattening.

## RO-Crate context fetching (online vs offline)

By default, tests fetch the official RO-Crate contexts from w3id.org.

- Online (default):

```bash
make test-online   # or just: make test
```

- Offline (uses local vendor copies):

```bash
make test-offline
```

Toggle is controlled by the ROCRATE_ONLINE env var (1 = online, 0 = offline).
In both modes, our own contexts under https://livepublication.org/interface-schemas/...
are rewritten to the local dev server (or BASE_URL for remote tests).

## Profile context (lp-dscdpc)

The profile context merges the DPC + DSC module contexts and adds PROV/xsd conveniences (`used`, `generated`, `startedAtTime`, `endedAtTime`). It is generated from the module contexts to avoid drift:

```bash
# generate/update profile
make build-profile

# verify the committed profile matches the modules
make check-profile
```

Use it in manifests (after RO-Crate contexts if present):

```json
"@context": [
  "https://w3id.org/ro/crate/1.1/context",
  "https://w3id.org/ro/terms/workflow-run/context",
  "https://livepublication.org/interface-schemas/contexts/lp-dscdpc/v1.jsonld"
]
```

## Modeling choices

### DSC I/O properties

DistributedStep uses **Schema.org properties** for inputs and outputs, aligned with `CreateAction`:

- **`object`** (input): The input resources or data consumed by the step
- **`result`** (output): The output resources or data produced by the step

At least one of `object` or `result` is required for conformance.

**Legacy PROV support**: `prov:used` and `prov:generated` are accepted for backward compatibility but are not normative and do not satisfy the conformance gate by themselves. New crates should use `object` and `result`.

Example:

```json
{
  "@id": "#step1",
  "@type": "DistributedStep",
  "hasPart": {"@id": "#runtime1"},
  "object": {"@id": "#input.txt"},
  "result": {"@id": "#output.txt"}
}
```

## Diagnostics & audits

The repository includes comprehensive diagnostic tools to track vocabulary usage, enforce policy, and monitor drift over time.

### Quick reference

```bash
make audit-vocab         # Vocabulary inventory (global + per-file)
make audit-vocab-offline # Offline mode (vendored contexts)
make audit-sparql        # SPARQL policy checks (fails on violations)
make audit-shapes        # SHACL shape coverage report
make coverage-all        # Run all diagnostic audits
```

All artifacts land in `.artifacts/` (git-ignored).

### 1. Vocabulary inventory (non-failing)

**What it does:**

- Walks all crates under `tests/crates/{valid,invalid}`
- Expands JSON-LD and converts to RDF
- Produces detailed vocabulary statistics

**Artifacts:**

- `.artifacts/vocab_inventory.json` — Global aggregates:

  - `by_namespace`: Predicate counts per namespace
  - `by_term`: Top 100 terms by usage
  - `classes_by_namespace`: Class usage
  - `literal_types`: XSD datatype distribution
  - `http_schema_terms`: HTTP schema.org violations (should be empty)
  - `unknown_namespaces`: Unrecognized namespaces
- `.artifacts/vocab_by_file.json` — Per-file breakdown of the above

**Run:**

```bash
make audit-vocab         # Online (fetches RO-Crate contexts)
make audit-vocab-offline # Offline (vendored contexts)
```

### 2. SPARQL policy checks (failing)

**What it does:**

- Runs ASK queries from `tests/policy/queries/` against valid crates
- Enforces crisp policy rules with clear failure messages

**Current policies:**

1. **no_http_schema_org.rq** — No `http://schema.org/*` predicates (HTTPS only)
2. **distributed_step_io.rq** — DistributedStep must have `schema:object` or `schema:result`
3. **control_action_target.rq** — ControlAction must target a DistributedStep
4. **requires_subscription_boolean.rq** — `schema:requiresSubscription` must be `xsd:boolean`
5. **content_size_integer.rq** — `schema:contentSize` must be `xsd:integer`
6. **date_time_types.rq** — Date/time properties must use `xsd:date` or `xsd:dateTime`

**Run:**

```bash
make audit-sparql
```

**Failure example:**

```
[SPARQL POLICY] requires_subscription_boolean failed for 2 crate(s):
  File: tests/crates/valid/dsc_full_02.json
    s=http://localhost:.../node v=False
```

**Adding new policies:**

1. Create a `.rq` file under `tests/policy/queries/`
2. Write an ASK query that returns `true` when the policy is violated
3. Run `make audit-sparql` to validate

### 3. SHACL shape coverage (non-failing)

**What it does:**

- Validates all valid crates with SHACL
- Tracks which shapes are actually exercised
- Identifies shapes with zero coverage (dead or over-narrow shapes)

**Artifact:**

- `.artifacts/shapes_coverage.json` — Per-shape statistics:
  - `files`: Which crates exercise the shape
  - `total_nodes`: Number of nodes validated
  - `total_violations`: Number of violations found
  - `example_nodes`: Sample node IRIs

**Run:**

```bash
make audit-shapes
```

**Output:**

```
[COVERAGE] Total shapes defined: 15
[COVERAGE] Shapes exercised: 12
[COVERAGE] Zero-coverage shapes: 3
  - http://example.org/shapes#UnusedShape
  - ...
```

### 4. Vocabulary baseline drift (failing)

**What it does:**

- Compares current vocabulary against committed baseline
- Catches unexpected namespace/term changes
- Enforces stability for critical terms

**Baseline:**

- `tests/fixtures/vocab_baseline.json` (committed)
- Generated from current crates; reviewed and committed

**Run:**

```bash
pytest tests/test_vocab_baseline.py
```

**Failure conditions:**

- New namespaces appear (not in allowlist)
- `http://schema.org/*` reappears
- Critical terms disappear or change >20%

**Update baseline:**

```bash
VOCAB_BASELINE_UPDATE=1 pytest tests/test_vocab_baseline.py
git diff tests/fixtures/vocab_baseline.json  # Review changes
git add tests/fixtures/vocab_baseline.json
git commit -m "chore: update vocab baseline"
```

### Running diagnostics offline

All audit targets support offline validation (vendored RO-Crate contexts):

```bash
ROCRATE_ONLINE=0 make audit-vocab
ROCRATE_ONLINE=0 make audit-sparql
ROCRATE_ONLINE=0 make coverage-all
```

### CI integration

**Diagnostics job (non-blocking):**

```yaml
- make coverage-all
```

**Required checks:**

```yaml
- make audit-sparql  # Enforce policy violations
- pytest tests/test_vocab_baseline.py  # Catch drift
```
