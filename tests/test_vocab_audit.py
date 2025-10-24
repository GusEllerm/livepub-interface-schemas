"""
Vocabulary audit: inventory and contract checks across all crates.

Produces a JSON artifact at .artifacts/vocab_inventory.json with:
- by_namespace: counts of predicates per namespace
- by_term: counts per full predicate IRI (top 100)
- classes_by_namespace: counts of rdf:type IRIs by namespace
- literals: counts by XSD datatype
- http_schema_terms: list of any http://schema.org/* predicates found
- unknown_namespaces: any predicate namespaces not in the allowlist

Contract checks (run only over tests/crates/valid):
- Assert no http://schema.org/* predicates
- Assert native XSD types for booleans/numbers
"""

import json
import pathlib
from collections import Counter
from typing import Iterator, Dict, Set, Any

import rdflib as rdf

from tests._jsonld_utils import to_rdf_graph_from_jsonld

# --- Configuration ---

CRATES_DIRS = ["tests/crates/valid", "tests/crates/invalid"]
ARTIFACT_DIR = pathlib.Path(".artifacts")
ARTIFACT_DIR.mkdir(exist_ok=True)
ARTIFACT_PATH = ARTIFACT_DIR / "vocab_inventory.json"
ARTIFACT_BY_FILE_PATH = ARTIFACT_DIR / "vocab_by_file.json"

ALLOWED_NS = {
    "https://schema.org/",
    "http://www.w3.org/ns/prov#",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "http://www.w3.org/2000/01/rdf-schema#",
    "http://www.w3.org/2001/XMLSchema#",
    "https://w3id.org/ro/crate/1.1/",
    "https://w3id.org/ro/terms/workflow-run#",
    "https://livepublication.org/interface-schemas/dpc#",
    "https://livepublication.org/interface-schemas/dsc#",
    "http://purl.org/dc/terms/",  # Dublin Core Terms (RO-Crate conformsTo)
    "https://bioschemas.org/",  # Bioschemas (ComputationalWorkflow)
    "https://bioschemas.org/ComputationalWorkflow#",  # Bioschemas fragment
}

# Expected schema.org terms we regularly use (for future warnings)
EXPECTED_SCHEMA_TERMS = {
    "https://schema.org/object",
    "https://schema.org/result",
    "https://schema.org/hasPart",
    "https://schema.org/step",
    "https://schema.org/additionalProperty",
    "https://schema.org/identifier",
    "https://schema.org/sourceOrganization",
    "https://schema.org/position",
    "https://schema.org/name",
    "https://schema.org/description",
    "https://schema.org/image",
    "https://schema.org/value",
    "https://schema.org/valueReference",
    "https://schema.org/observationAbout",
    "https://schema.org/minValue",
    "https://schema.org/maxValue",
    "https://schema.org/measurementTechnique",
    "https://schema.org/input",
    "https://schema.org/output",
    "https://schema.org/exampleOfWork",
    "https://schema.org/agent",
    "https://schema.org/instrument",
    "https://schema.org/actionStatus",
    "https://schema.org/startTime",
    "https://schema.org/endTime",
    "https://schema.org/mainEntity",
    "https://schema.org/conformsTo",
    "https://schema.org/datePublished",
    "https://schema.org/license",
    "https://schema.org/programmingLanguage",
    "https://schema.org/about",
}

# --- Helper functions ---


def _ns(iri: str) -> str:
    """Extract namespace from IRI (split on last '#', else last '/')."""
    if "#" in iri:
        return iri.rsplit("#", 1)[0] + "#"
    return iri.rsplit("/", 1)[0] + "/"


def _iter_crate_files(dirs: list[str]) -> Iterator[pathlib.Path]:
    """Yield all .json files under the given directories."""
    for d in dirs:
        p = pathlib.Path(d)
        if p.exists():
            for f in sorted(p.glob("**/*.json")):
                yield f


def _load_graph(path: pathlib.Path, base_override: str) -> rdf.Graph:
    """Load a JSON-LD crate and convert to rdflib Graph."""
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    return to_rdf_graph_from_jsonld(doc, base_override)


def _inventory_single_file(path: pathlib.Path, base_override: str) -> Dict[str, Any]:
    """
    Produce vocabulary inventory for a single crate file.
    
    Returns dict with same structure as _inventory but for one file.
    """
    by_ns = Counter()
    by_term = Counter()
    classes_by_ns = Counter()
    http_schema_terms: Set[str] = set()
    unknown_ns: Set[str] = set()
    literal_types = Counter()

    try:
        g = _load_graph(path, base_override)
    except Exception as e:
        return {
            "error": str(e),
            "predicates_by_namespace": [],
            "terms": [],
            "classes_by_namespace": [],
            "literal_types": [],
            "http_schema_terms": [],
            "unknown_namespaces": [],
        }

    # Walk all triples
    for s, p, o in g.triples((None, None, None)):
        # Predicates
        if isinstance(p, rdf.term.URIRef):
            piri = str(p)
            by_term[piri] += 1
            ns = _ns(piri)
            by_ns[ns] += 1
            
            # Flag http://schema.org/* predicates
            if piri.startswith("http://schema.org/"):
                http_schema_terms.add(piri)

        # Literal datatypes
        if isinstance(o, rdf.term.Literal) and o.datatype:
            literal_types[str(o.datatype)] += 1

        # Classes (rdf:type objects)
        if p == rdf.RDF.type and isinstance(o, rdf.term.URIRef):
            classes_by_ns[_ns(str(o))] += 1

    # Identify unknown namespaces
    for ns in by_ns:
        if ns not in ALLOWED_NS:
            unknown_ns.add(ns)

    return {
        "predicates_by_namespace": by_ns.most_common(),
        "terms": by_term.most_common(50),  # Top 50 per file
        "classes_by_namespace": classes_by_ns.most_common(),
        "literal_types": literal_types.most_common(),
        "http_schema_terms": sorted(http_schema_terms),
        "unknown_namespaces": sorted(unknown_ns),
    }


def _inventory(paths: list[pathlib.Path], base_override: str) -> Dict[str, Any]:
    """
    Produce vocabulary inventory across all given crate paths.
    
    Returns dict with:
    - by_namespace: [(namespace, count), ...]
    - by_term: [(term_iri, count), ...] (top 100)
    - classes_by_namespace: [(namespace, count), ...]
    - literal_types: [(datatype_iri, count), ...]
    - http_schema_terms: [iri, ...] (any http://schema.org/* predicates)
    - unknown_namespaces: [ns, ...] (not in allowlist)
    """
    by_ns = Counter()
    by_term = Counter()
    classes_by_ns = Counter()
    http_schema_terms: Set[str] = set()
    unknown_ns: Set[str] = set()
    literal_types = Counter()

    for path in paths:
        try:
            g = _load_graph(path, base_override)
        except Exception as e:
            print(f"[VOCAB AUDIT] Warning: could not load {path}: {e}")
            continue

        # Walk all triples
        for s, p, o in g.triples((None, None, None)):
            # Predicates
            if isinstance(p, rdf.term.URIRef):
                piri = str(p)
                by_term[piri] += 1
                ns = _ns(piri)
                by_ns[ns] += 1
                
                # Flag http://schema.org/* predicates
                if piri.startswith("http://schema.org/"):
                    http_schema_terms.add(piri)

            # Literal datatypes
            if isinstance(o, rdf.term.Literal) and o.datatype:
                literal_types[str(o.datatype)] += 1

            # Classes (rdf:type objects)
            if p == rdf.RDF.type and isinstance(o, rdf.term.URIRef):
                classes_by_ns[_ns(str(o))] += 1

    # Identify unknown namespaces
    for ns in by_ns:
        if ns not in ALLOWED_NS:
            unknown_ns.add(ns)

    return {
        "by_namespace": by_ns.most_common(),
        "by_term": by_term.most_common(100),
        "classes_by_namespace": classes_by_ns.most_common(),
        "literal_types": literal_types.most_common(),
        "http_schema_terms": sorted(http_schema_terms),
        "unknown_namespaces": sorted(unknown_ns),
    }


# --- Test functions ---


def test_vocab_inventory_report(server_base):
    """
    Generate vocabulary inventory report (non-failing).
    
    Writes JSON artifacts:
    - .artifacts/vocab_inventory.json (global)
    - .artifacts/vocab_by_file.json (per-file breakdown)
    
    Prints brief summary to stdout.
    """
    paths = list(_iter_crate_files(CRATES_DIRS))
    inv = _inventory(paths, server_base)
    
    # Global inventory
    with open(ARTIFACT_PATH, "w", encoding="utf-8") as fh:
        json.dump(inv, fh, indent=2, ensure_ascii=False)
    
    # Per-file inventory
    by_file = {}
    cwd = pathlib.Path.cwd()
    for path in paths:
        try:
            rel_path = str(path.relative_to(cwd))
        except ValueError:
            # Path not relative to cwd, use absolute
            rel_path = str(path)
        by_file[rel_path] = _inventory_single_file(path, server_base)
    
    with open(ARTIFACT_BY_FILE_PATH, "w", encoding="utf-8") as fh:
        json.dump(by_file, fh, indent=2, ensure_ascii=False)
    
    # Brief stdout summary
    print("\n=== Vocabulary Inventory Report ===")
    print(f"[VOCAB] Processed {len(paths)} crate files")
    print(f"[VOCAB] Top 5 namespaces: {inv['by_namespace'][:5]}")
    print(f"[VOCAB] Top 10 terms:")
    for term, count in inv["by_term"][:10]:
        print(f"  {term}: {count}")
    print(f"[VOCAB] Literal types: {dict(inv['literal_types'])}")
    print(f"[VOCAB] HTTP schema.org terms: {inv['http_schema_terms'] or 'None (✓)'}")
    print(f"[VOCAB] Unknown namespaces: {inv['unknown_namespaces'] or 'None (✓)'}")
    print(f"[VOCAB] Global artifact: {ARTIFACT_PATH.absolute()}")
    print(f"[VOCAB] Per-file artifact: {ARTIFACT_BY_FILE_PATH.absolute()}")
    print("=" * 40)
    
    # Print per-file summary if verbose
    import os
    if os.getenv("PYTEST_CURRENT_TEST") and "-v" in os.getenv("PYTEST_CURRENT_TEST", ""):
        print("\n[VOCAB] Per-file summary:")
        for rel_path, file_inv in by_file.items():
            if "error" in file_inv:
                print(f"  {rel_path}: ERROR - {file_inv['error']}")
            else:
                ns_count = sum(c for _, c in file_inv["predicates_by_namespace"])
                print(f"  {rel_path}: {ns_count} predicates, "
                      f"{len(file_inv['http_schema_terms'])} HTTP schema.org terms")
    
    # Always pass - this is report-only
    assert True


def test_valid_crates_vocab_contract(server_base):
    """
    Enforce vocabulary contract on valid crates only.
    
    Checks:
    1. No http://schema.org/* predicates (must be HTTPS)
    2. Native XSD types present for booleans/numbers
    """
    paths = list(_iter_crate_files(["tests/crates/valid"]))
    inv = _inventory(paths, server_base)
    
    # 1) No http://schema.org/* predicates in valid crates
    assert not inv["http_schema_terms"], (
        f"Found http://schema.org/* terms in valid crates (must be HTTPS): "
        f"{inv['http_schema_terms']}"
    )
    
    # 2) Ensure we see native booleans/numbers (at least some)
    #    This catches regressions where everything became xsd:string
    lt = dict(inv["literal_types"])
    
    has_boolean = any("boolean" in str(t).lower() for t in lt.keys())
    has_numeric = any(
        any(num_type in str(t).lower() for num_type in ["double", "integer", "decimal", "float"])
        for t in lt.keys()
    )
    
    assert has_boolean or has_numeric, (
        f"Expected some native boolean/number literals in valid crates; "
        f"saw types: {lt}"
    )
    
    print("\n[VOCAB CONTRACT] ✓ Valid crates passed vocab contract checks")
    print(f"  - No http://schema.org/* predicates")
    print(f"  - Native XSD types present: {[t for t in lt.keys() if 'boolean' in str(t).lower() or any(n in str(t).lower() for n in ['double', 'integer', 'decimal'])]}")
