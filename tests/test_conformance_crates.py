"""
SHACL conformance tests for valid crates.

Tests are automatically parametrized over all files in tests/crates/valid/.
Adding or removing files changes the test set automatically.
"""

import json
from pyshacl import validate
from rdflib import Graph
from tests._jsonld_utils import to_rdf_graph_from_jsonld


def _load_shapes_graph(server_base: str) -> Graph:
    """Load both DPC and DSC SHACL shapes into a single graph."""
    g = Graph()
    g.parse(f"{server_base}/dpc/shapes.ttl", format="turtle")
    g.parse(f"{server_base}/dsc/shapes.ttl", format="turtle")
    return g


def test_valid_crate_conforms(server_base, valid_crate_path):
    """
    Valid crates must pass SHACL validation.
    
    Parametrized over all files in tests/crates/valid/ via conftest.py.
    """
    with open(valid_crate_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    data_graph = to_rdf_graph_from_jsonld(data, base_override=server_base)
    shapes_graph = _load_shapes_graph(server_base)
    
    conforms, report_graph, report_text = validate(
        data_graph,
        shacl_graph=shapes_graph,
        inference='rdfs',
        serialize_report_graph=True
    )
    
    assert conforms, (
        f"Expected VALID but got violations for {valid_crate_path}:\n"
        f"{report_text}"
    )
