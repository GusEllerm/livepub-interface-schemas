import glob
import json
import pytest
from pyshacl import validate
from rdflib import Graph
from _jsonld_utils import to_rdf_graph_from_jsonld

VALID = sorted(glob.glob("tests/crates/valid/*.json"))


def _load_shapes_graph(server_base: str) -> Graph:
    """Load both DPC and DSC SHACL shapes into a single graph."""
    g = Graph()
    g.parse(f"{server_base}/dpc/shapes.ttl", format="turtle")
    g.parse(f"{server_base}/dsc/shapes.ttl", format="turtle")
    return g


@pytest.mark.parametrize("path", VALID)
def test_valid_crates_conform(server_base, path):
    """Valid crates must pass SHACL validation."""
    with open(path, "r", encoding="utf-8") as f:
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
        f"Expected VALID but got violations for {path}:\n"
        f"{report_text}"
    )

