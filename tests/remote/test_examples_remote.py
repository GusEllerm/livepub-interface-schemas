import glob, os, pytest
from rdflib import Graph
from pyshacl import validate
from _jsonld_utils import load_json_file, expand_with_override, to_rdf_graph_from_jsonld

BASE_URL = os.environ.get("BASE_URL")  # e.g., https://livepublication.org/interface-schemas
pytestmark = pytest.mark.skipif(not BASE_URL, reason="Set BASE_URL to run remote tests")

EXAMPLES = sorted(glob.glob("tests/test_json/**/*.json", recursive=True)) + sorted(glob.glob("tests/test_json/*.json"))


def test_all_examples_expand_remotely():
    for path in EXAMPLES:
        doc = load_json_file(path)
        expanded = expand_with_override(doc, base_override=BASE_URL)
        assert expanded and isinstance(expanded, list), f"Expand failed for {path}"


def test_all_examples_validate_shacl_remotely():
    # Load shapes from remote
    dpc_shapes = Graph().parse(f"{BASE_URL}/dpc/shapes.ttl")
    dsc_shapes = Graph().parse(f"{BASE_URL}/dsc/shapes.ttl")

    for path in EXAMPLES:
        g = Graph()
        doc = load_json_file(path)
        to_rdf_graph_from_jsonld(doc, base_override=BASE_URL, rdflib_graph=g)

        conforms1, _, rep1 = validate(g, shacl_graph=dpc_shapes, inference='rdfs', debug=False)
        conforms2, _, rep2 = validate(g, shacl_graph=dsc_shapes, inference='rdfs', debug=False)
        assert conforms1 and conforms2, f"SHACL failed for {path}\nDPC:\n{rep1}\nDSC:\n{rep2}"
