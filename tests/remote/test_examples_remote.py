"""Remote round-trip tests for valid example crates."""
import json
import os
import pytest
import sys
from rdflib import Graph
from pyshacl import validate
from _jsonld_utils import expand_with_override, to_rdf_graph_from_jsonld

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from _example_loader import list_valid_examples

BASE_URL = os.environ.get("BASE_URL", "")  # e.g., https://livepublication.org/interface-schemas
pytestmark = pytest.mark.skipif(not BASE_URL, reason="Set BASE_URL to run remote tests")


@pytest.mark.parametrize("path", list_valid_examples())
def test_remote_expand_and_parse_to_graph(path):
    """Valid examples must expand against remote contexts and produce a non-empty RDF graph."""
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    expanded = expand_with_override(doc, base_override=BASE_URL)
    assert expanded and isinstance(expanded, list), f"Expand failed for {path}"
    
    g = to_rdf_graph_from_jsonld(doc, base_override=BASE_URL)
    assert len(g) > 0, f"Empty graph for {path}"


@pytest.mark.parametrize("path", list_valid_examples())
def test_remote_examples_conform_to_shacl(path):
    """Valid examples must pass SHACL validation against remote shapes."""
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    g = to_rdf_graph_from_jsonld(doc, base_override=BASE_URL)

    # Load shapes from remote
    dpc_shapes = Graph().parse(f"{BASE_URL}/dpc/shapes.ttl", format="turtle")
    dsc_shapes = Graph().parse(f"{BASE_URL}/dsc/shapes.ttl", format="turtle")

    conforms1, _, rep1 = validate(g, shacl_graph=dpc_shapes, inference='rdfs', debug=False)
    conforms2, _, rep2 = validate(g, shacl_graph=dsc_shapes, inference='rdfs', debug=False)
    assert conforms1 and conforms2, f"SHACL failed for {path}\nDPC:\n{rep1}\nDSC:\n{rep2}"
