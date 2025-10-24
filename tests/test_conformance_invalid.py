"""
SHACL conformance tests for invalid crates.

Tests are automatically parametrized over all files in tests/crates/invalid/.
If the directory is empty, tests skip gracefully.
"""

import json
import pytest
from pyshacl import validate
from rdflib import Graph
from tests._jsonld_utils import to_rdf_graph_from_jsonld


def _load_shapes_graph(server_base: str) -> Graph:
    """Load both DPC and DSC SHACL shapes into a single graph."""
    g = Graph()
    g.parse(f"{server_base}/dpc/shapes.ttl", format="turtle")
    g.parse(f"{server_base}/dsc/shapes.ttl", format="turtle")
    return g


def test_invalid_crate_violates(server_base, invalid_crate_path):
    """
    Invalid crates should fail SHACL validation.
    
    Parametrized over all files in tests/crates/invalid/ via conftest.py.
    If no invalid crates exist, this test is skipped automatically.
    """
    with open(invalid_crate_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    data_graph = to_rdf_graph_from_jsonld(data, base_override=server_base)
    shapes_graph = _load_shapes_graph(server_base)
    
    conforms, report_graph, report_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference='rdfs',
        serialize_report_graph=True
    )
    
    assert not conforms, (
        f"Expected INVALID to have violations, but {invalid_crate_path} conformed!\n"
        f"This file should be moved to tests/crates/valid/ or fixed to trigger violations."
    )
    
    # Print violations for debugging
    print(f"\n{invalid_crate_path} violations:\n{report_text}")
