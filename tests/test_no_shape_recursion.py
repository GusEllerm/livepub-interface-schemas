import warnings, json, glob
from pyshacl import validate
from pyshacl.constraints.core.shape_based_constraints import ShapeRecursionWarning
from rdflib import Graph
from _jsonld_utils import to_rdf_graph_from_jsonld

VALID = sorted(glob.glob("tests/crates/valid/*.json"))


def _load_shapes(server_base: str) -> Graph:
    g = Graph()
    g.parse(f"{server_base}/dpc/shapes.ttl", format="turtle")
    g.parse(f"{server_base}/dsc/shapes.ttl", format="turtle")
    return g


def test_no_shape_recursion_on_valid_examples(server_base):
    shapes = _load_shapes(server_base)
    with warnings.catch_warnings():
        warnings.filterwarnings("error", category=ShapeRecursionWarning)
        for path in VALID:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data_g = to_rdf_graph_from_jsonld(data, base_override=server_base)
            conforms, report, report_text = validate(
                data_g, shacl_graph=shapes, inference="rdfs", serialize_report_graph=True
            )
            assert conforms, f"Conformance failed for {path}:\n{report_text}"
