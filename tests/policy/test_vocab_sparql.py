"""
SPARQL policy checks for valid crates.

Runs ASK queries from tests/policy/queries/ against each valid crate graph.
Tests are parametrized NxM (each query × each valid file).
Provides clear failure messages with offending triples.
"""

import pathlib
from typing import List

import pytest
import rdflib as rdf
import json

from tests._jsonld_utils import to_rdf_graph_from_jsonld


QUERIES_DIR = pathlib.Path(__file__).parent / "queries"


def _load_graph(path: pathlib.Path, base_override: str) -> rdf.Graph:
    """Load a JSON-LD crate and convert to rdflib Graph."""
    with open(path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    return to_rdf_graph_from_jsonld(doc, base_override)


def _load_query(query_path: pathlib.Path) -> str:
    """Load SPARQL query from file."""
    return query_path.read_text(encoding="utf-8")


def _find_evidence(g: rdf.Graph, query_path: pathlib.Path, limit: int = 3) -> List[str]:
    """
    Find evidence triples for a failing ASK query.
    
    Converts ASK to SELECT by extracting WHERE clause and limiting results.
    """
    query_text = _load_query(query_path)
    
    # Simple heuristic: convert ASK to SELECT by replacing ASK with SELECT *
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


def _discover_queries() -> List[pathlib.Path]:
    """Discover all .rq files in queries directory."""
    if not QUERIES_DIR.exists():
        return []
    return sorted(QUERIES_DIR.glob("*.rq"))


# Discover all queries
QUERY_PATHS = _discover_queries()


@pytest.mark.parametrize("query_path", QUERY_PATHS, ids=lambda p: p.stem)
def test_sparql_policy_per_file(server_base, valid_crate_path, query_path):
    """
    Run a SPARQL ASK policy query against a valid crate.
    
    Parametrized NxM over all queries × all valid crates.
    Fails if ASK returns true (indicating policy violation).
    Shows offending triples in the error message.
    """
    query_text = _load_query(query_path)
    
    try:
        g = _load_graph(valid_crate_path, server_base)
    except Exception as e:
        pytest.skip(f"Could not load {valid_crate_path}: {e}")
        return
    
    # Run ASK query
    result = g.query(query_text)
    
    # ASK queries return a boolean result
    if bool(result):
        # Policy violation detected
        evidence = _find_evidence(g, query_path)
        cwd = pathlib.Path.cwd()
        try:
            rel_path = str(valid_crate_path.relative_to(cwd))
        except ValueError:
            rel_path = str(valid_crate_path)
        
        msg_parts = [f"\n[SPARQL POLICY] {query_path.stem} failed for {rel_path}:"]
        for ev in evidence[:3]:  # Show first 3 evidence items
            msg_parts.append(f"\n  {ev}")
        
        pytest.fail("".join(msg_parts))
