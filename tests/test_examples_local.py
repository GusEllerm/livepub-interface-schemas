import glob, os
from rdflib import Graph
from pyshacl import validate
from _jsonld_utils import load_json_file, expand_with_override, to_rdf_graph_from_jsonld

EXAMPLES = sorted(glob.glob("tests/test_json/**/*.json", recursive=True)) + sorted(glob.glob("tests/test_json/*.json"))


def test_examples_exist():
    # If you remove samples, keep this soft so the suite still passes.
    assert len(EXAMPLES) >= 1, "Place example manifests in tests/test_json/*.json"


def test_all_examples_expand_locally(server_base):
    base = server_base  # e.g., http://localhost:PORT/interface-schemas
    for path in EXAMPLES:
        doc = load_json_file(path)
        expanded = expand_with_override(doc, base_override=base)
        assert expanded and isinstance(expanded, list), f"Expand failed for {path}"


def test_all_examples_validate_shacl_locally(server_base):
    base = server_base
    # Load shapes once
    dpc_shapes = Graph().parse(f"{base}/dpc/shapes.ttl")
    dsc_shapes = Graph().parse(f"{base}/dsc/shapes.ttl")

    for path in EXAMPLES:
        g = Graph()
        doc = load_json_file(path)
        to_rdf_graph_from_jsonld(doc, base_override=base, rdflib_graph=g)

        # Validate against both shape graphs; only targeted classes will be checked
        conforms1, _, rep1 = validate(g, shacl_graph=dpc_shapes, inference='rdfs', debug=False)
        conforms2, _, rep2 = validate(g, shacl_graph=dsc_shapes, inference='rdfs', debug=False)

        # We accept if BOTH shapes don't apply (still conforms) or if they apply and pass.
        # If a shape applies and fails, pySHACL returns conforms=False.
        assert conforms1 and conforms2, f"SHACL failed for {path}\nDPC:\n{rep1}\nDSC:\n{rep2}"
