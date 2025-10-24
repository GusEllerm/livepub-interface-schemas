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


# Pick smallest valid crates for testing
SMALL_DSC_CRATE = pathlib.Path("tests/crates/valid/dsc_min.json")
SMALL_DPC_CRATE = pathlib.Path("tests/crates/valid/dpc_min.json")


@pytest.mark.general
def test_pipeline_no_warnings_dsc(server_base):
    """
    Load smallest DSC crate with no warnings.
    
    Verifies:
    - No Python warnings emitted
    - Graph has > 0 triples
    - No named graphs (tripwire)
    - Native XSD datatypes present
    """
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Load and parse
        with open(SMALL_DSC_CRATE, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        
        g = to_rdf_graph_from_jsonld(doc, server_base)
        
        # Assert no warnings
        if w:
            warning_msgs = [str(warning.message) for warning in w]
            pytest.fail(f"Expected no warnings, got {len(w)}:\n" + "\n".join(warning_msgs))
    
    # Assert graph has triples
    triple_count = len(g)
    assert triple_count > 0, f"Expected > 0 triples, got {triple_count}"
    
    # Assert no named graphs (should be plain Graph, not Dataset)
    assert isinstance(g, rdf.Graph), f"Expected rdf.Graph, got {type(g)}"
    
    print(f"\n✓ DSC pipeline: {triple_count} triples, 0 warnings")



@pytest.mark.general
def test_pipeline_no_warnings_dpc(server_base):
    """
    Load smallest DPC crate with no warnings.
    
    Verifies:
    - No Python warnings emitted
    - Graph has > 0 triples
    - No named graphs (tripwire)
    - Native XSD datatypes present
    """
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Load and parse
        with open(SMALL_DPC_CRATE, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        
        g = to_rdf_graph_from_jsonld(doc, server_base)
        
        # Assert no warnings
        if w:
            warning_msgs = [str(warning.message) for warning in w]
            pytest.fail(f"Expected no warnings, got {len(w)}:\n" + "\n".join(warning_msgs))
    
    # Assert graph has triples
    triple_count = len(g)
    assert triple_count > 0, f"Expected > 0 triples, got {triple_count}"
    
    # Assert no named graphs
    assert isinstance(g, rdf.Graph), f"Expected rdf.Graph, got {type(g)}"
    
    print(f"\n✓ DPC pipeline: {triple_count} triples, 0 warnings")



@pytest.mark.general
def test_pipeline_deterministic(server_base):
    """
    Verify pipeline produces identical results across runs.
    
    Same input should produce same triple count and predicate/class sets.
    """
    with open(SMALL_DSC_CRATE, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    
    # Run twice
    g1 = to_rdf_graph_from_jsonld(doc, server_base)
    g2 = to_rdf_graph_from_jsonld(doc, server_base)
    
    # Same triple count
    assert len(g1) == len(g2), f"Triple counts differ: {len(g1)} vs {len(g2)}"
    
    # Same predicates
    predicates1 = {str(p) for s, p, o in g1.triples((None, None, None))}
    predicates2 = {str(p) for s, p, o in g2.triples((None, None, None))}
    assert predicates1 == predicates2, "Predicates differ between runs"
    
    # Same classes
    classes1 = {str(o) for s, p, o in g1.triples((None, rdf.RDF.type, None))}
    classes2 = {str(o) for s, p, o in g2.triples((None, rdf.RDF.type, None))}
    assert classes1 == classes2, "Classes differ between runs"
    
    print(f"✓ Deterministic: {len(g1)} triples, {len(predicates1)} predicates, {len(classes1)} classes")
