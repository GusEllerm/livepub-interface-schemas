from rdflib import Graph, Namespace, RDF, RDFS

DPC = Namespace("https://livepublication.org/interface-schemas/dpc#")


def test_terms_and_shapes_parse(server_base):
    g_terms = Graph().parse(f"{server_base}/dpc/terms.ttl")
    g_shapes = Graph().parse(f"{server_base}/dpc/shapes.ttl")

    # Basic sanity: classes exist
    assert (DPC.HardwareRuntime, RDF.type, RDFS.Class) in g_terms
    assert (DPC.HardwareComponent, RDF.type, RDFS.Class) in g_terms

    # Properties exist
    assert (DPC.component, RDF.type, None) in g_terms
    assert (DPC.performance, RDF.type, None) in g_terms

    # Shapes parses (we don't assert SHACL triples here beyond parse success)
    assert len(g_shapes) > 0
