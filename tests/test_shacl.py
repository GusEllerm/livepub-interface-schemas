from rdflib import Graph
from pyshacl import validate


data_g = Graph().parse("tests/data_dpc.ttl", format="turtle")
shapes_g = Graph().parse("interface-schemas/dpc/shapes.ttl", format="turtle")

conforms, report_g, report_text = validate(data_g, shacl_graph=shapes_g, inference='rdfs', debug=False)
print(report_text)
assert conforms, "SHACL validation failed"
print("OK: SHACL validation passed.")
