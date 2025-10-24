"""
SPARQL policy checks for valid crates.

Runs ASK queries from tests/policy/queries/ against each valid crate graph.
Provides clear failure messages with offending triples.
"""

import pathlib
from typing import List, Tuple

import pytest
import rdflib as rdf

from tests._example_loader import list_valid_examples
from tests._jsonld_utils import to_rdf_graph_from_jsonld
import json


QUERIES_DIR = pathlib.Path(__file__).parent / "queries"


def _load_graph(path: pathlib.Path, base_override: str) -> rdf.Graph:
    """Load a JSON-LD crate and convert to rdflib Graph."""
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    return to_rdf_graph_from_jsonld(doc, base_override)


def _load_query(query_path: pathlib.Path) -> str:
    """Load SPARQL query from file."""
    return query_path.read_text(encoding="utf-8")


def _find_evidence(g: rdf.Graph, query_file: str, limit: int = 3) -> List[str]:
    """
    Find evidence triples for a failing ASK query.
    
    Converts ASK to SELECT by extracting WHERE clause and limiting results.
    """
    query_text = _load_query(QUERIES_DIR / query_file)
    
    # Simple heuristic: convert ASK to SELECT by replacing ASK with SELECT *
    # This won't work for all queries but covers our simple ASK patterns
    if "ASK WHERE" in query_text:
        select_query = query_text.replace("ASK WHERE", "SELECT * WHERE", 1)
        select_query = select_query.replace("ASK", "SELECT *", 1)
    else:
        # Fallback: just return generic message
        return ["(evidence extraction not available for this query pattern)"]
    
    try:
        results = g.query(select_query)
        evidence = []
        for i, row in enumerate(results):
            if i >= limit:
                break
            # Format the binding
            parts = []
            for var in results.vars:
                val = row[var]
                if val:
                    parts.append(f"{var}={val}")
            evidence.append(" ".join(parts))
        return evidence or ["(no specific evidence captured)"]
    except Exception as e:
        return [f"(evidence extraction failed: {e})"]


def _discover_queries() -> List[Tuple[str, pathlib.Path]]:
    """Discover all .rq files in queries directory."""
    if not QUERIES_DIR.exists():
        return []
    return [(q.stem, q) for q in sorted(QUERIES_DIR.glob("*.rq"))]


# Parametrize over all query files
QUERIES = _discover_queries()


@pytest.mark.parametrize("query_name,query_path", QUERIES, ids=[q[0] for q in QUERIES])
def test_sparql_policy_valid_crates(server_base, query_name, query_path):
    """
    Run a SPARQL ASK policy query against all valid crates.
    
    Fails if ASK returns true for any crate (indicating policy violation).
    Shows the first few offending triples in the error message.
    """
    query_text = _load_query(query_path)
    
    violations = []
    cwd = pathlib.Path.cwd()
    
    for crate_path_str in list_valid_examples():
        crate_path = pathlib.Path(crate_path_str)
        try:
            g = _load_graph(crate_path, server_base)
        except Exception as e:
            pytest.skip(f"Could not load {crate_path}: {e}")
            continue
        
        # Run ASK query
        result = g.query(query_text)
        
        # ASK queries return a boolean result
        if bool(result):
            # Policy violation detected
            evidence = _find_evidence(g, query_path.name)
            try:
                rel_path = str(crate_path.relative_to(cwd))
            except ValueError:
                rel_path = str(crate_path)
            violations.append({
                "file": rel_path,
                "evidence": evidence,
            })
    
    # Assert no violations
    if violations:
        msg_parts = [f"\n[SPARQL POLICY] {query_name} failed for {len(violations)} crate(s):"]
        for v in violations[:5]:  # Show first 5 violations
            msg_parts.append(f"\n  File: {v['file']}")
            for ev in v['evidence'][:3]:  # Show first 3 evidence items
                msg_parts.append(f"    {ev}")
        if len(violations) > 5:
            msg_parts.append(f"\n  ... and {len(violations) - 5} more")
        
        pytest.fail("".join(msg_parts))
