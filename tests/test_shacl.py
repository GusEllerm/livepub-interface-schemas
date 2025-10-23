from rdflib import Graph
from pyshacl import validate


def test_shacl_dpc_local_files():
    data_g = Graph().parse("tests/data_dpc.ttl", format="turtle")
    shapes_g = Graph().parse("interface-schemas/dpc/shapes.ttl", format="turtle")
    conforms, _, report = validate(data_g, shacl_graph=shapes_g, inference='rdfs', debug=False)
    assert conforms, report
