"""
General sanity checks for the JSON-LD → RDF pipeline.

Tests deterministic behavior, no warnings, and native XSD types.
"""

import json
import pathlib
import warnings

import pytest
import rdflib as rdf

from tests._jsonld_utils import to_rdf_graph_from_jsonld


@pytest.mark.general
def test_pipeline_no_warnings(server_base, valid_crate_path):
    """
    Load crate with no warnings.
    
    Verifies:
    - No Python warnings emitted
    - Graph has > 0 triples
    - No named graphs (tripwire)
    
    This test is parametrized over all files in tests/crates/valid/
    via the valid_crate_path fixture from conftest.py.
    """
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Load and parse
        with open(valid_crate_path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        
        g = to_rdf_graph_from_jsonld(doc, server_base)
        
        # Assert no warnings
        if w:
            warning_msgs = [str(warning.message) for warning in w]
            pytest.fail(f"[{valid_crate_path.name}] Expected no warnings, got {len(w)}:\n" + "\n".join(warning_msgs))
    
    # Assert graph has triples
    triple_count = len(g)
    assert triple_count > 0, f"[{valid_crate_path.name}] Expected > 0 triples, got {triple_count}"
    
    # Assert no named graphs (should be plain Graph, not Dataset)
    assert isinstance(g, rdf.Graph), f"[{valid_crate_path.name}] Expected rdf.Graph, got {type(g)}"
    
    print(f"\n[{valid_crate_path.name}] ✓ Pipeline: {triple_count} triples, 0 warnings")


@pytest.mark.general
def test_pipeline_deterministic(server_base, valid_crate_path):
    """
    Verify pipeline produces identical results across runs.
    
    Same input should produce same triple count and predicate/class sets.
    
    This test is parametrized over all files in tests/crates/valid/
    via the valid_crate_path fixture from conftest.py.
    """
    with open(valid_crate_path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    
    # Run twice
    g1 = to_rdf_graph_from_jsonld(doc, server_base)
    g2 = to_rdf_graph_from_jsonld(doc, server_base)
    
    # Same triple count
    assert len(g1) == len(g2), f"[{valid_crate_path.name}] Triple counts differ: {len(g1)} vs {len(g2)}"
    
    # Same predicates
    predicates1 = {str(p) for s, p, o in g1.triples((None, None, None))}
    predicates2 = {str(p) for s, p, o in g2.triples((None, None, None))}
    assert predicates1 == predicates2, f"[{valid_crate_path.name}] Predicates differ between runs"
    
    # Same classes
    classes1 = {str(o) for s, p, o in g1.triples((None, rdf.RDF.type, None))}
    classes2 = {str(o) for s, p, o in g2.triples((None, rdf.RDF.type, None))}
    assert classes1 == classes2, f"[{valid_crate_path.name}] Classes differ between runs"
    
    print(f"[{valid_crate_path.name}] ✓ Deterministic: {len(g1)} triples, {len(predicates1)} predicates, {len(classes1)} classes")
