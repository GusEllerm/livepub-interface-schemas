"""Local round-trip tests for valid example crates."""
import json
import pytest
from rdflib import Graph
from pyshacl import validate
from _jsonld_utils import expand_with_override, to_rdf_graph_from_jsonld
from _example_loader import list_valid_examples


@pytest.mark.parametrize("path", list_valid_examples())
def test_expand_and_parse_to_graph(server_base, path):
    """Valid examples must expand and produce a non-empty RDF graph."""
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    expanded = expand_with_override(doc, base_override=server_base)
    assert expanded and isinstance(expanded, list), f"Expand failed for {path}"
    
    g = to_rdf_graph_from_jsonld(doc, base_override=server_base)
    assert len(g) > 0, f"Empty graph for {path}"


@pytest.mark.parametrize("path", list_valid_examples())
def test_valid_examples_conform_to_shacl(server_base, path):
    """Valid examples must pass SHACL validation."""
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    g = to_rdf_graph_from_jsonld(doc, base_override=server_base)

    # Load shapes
    dpc_shapes = Graph().parse(f"{server_base}/dpc/shapes.ttl", format="turtle")
    dsc_shapes = Graph().parse(f"{server_base}/dsc/shapes.ttl", format="turtle")

    # Validate against both shape graphs
    conforms1, _, rep1 = validate(g, shacl_graph=dpc_shapes, inference='rdfs', debug=False)
    conforms2, _, rep2 = validate(g, shacl_graph=dsc_shapes, inference='rdfs', debug=False)

    assert conforms1 and conforms2, f"SHACL failed for {path}\nDPC:\n{rep1}\nDSC:\n{rep2}"
