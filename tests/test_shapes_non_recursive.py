from rdflib import Graph, Namespace
from rdflib.namespace import NamespaceManager
import pytest

SH = Namespace("http://www.w3.org/ns/shacl#")
SCHEMA = Namespace("https://schema.org/")
DPC = Namespace("https://livepublication.org/interface-schemas/dpc#")
DSC = Namespace("https://livepublication.org/interface-schemas/dsc#")


@pytest.fixture
def shapes(server_base):
    g = Graph()
    g.parse(f"{server_base}/dpc/shapes.ttl", format="turtle")
    g.parse(f"{server_base}/dsc/shapes.ttl", format="turtle")
    nm = NamespaceManager(g)
    nm.bind("sh", SH); nm.bind("schema", SCHEMA); nm.bind("dpc", DPC); nm.bind("dsc", DSC)
    g.namespace_manager = nm
    return g


def _property_shapes_for_path(g, path_iri):
    # Return all blank nodes that are property shapes with sh:path == path_iri
    for ps in g.subjects(predicate=SH.path, object=path_iri):
        yield ps


def test_dpc_component_uses_class_not_node(shapes):
    found = False
    for ps in _property_shapes_for_path(shapes, DPC.component):
        found = True
        assert (ps, SH["class"], DPC.HardwareComponent) in shapes, "dpc:component must use sh:class dpc:HardwareComponent"
        assert not list(shapes.objects(ps, SH.node)), "dpc:component must not use sh:node (to avoid recursion)"
    assert found, "No property shape found for dpc:component"


def test_dpc_performance_uses_class_not_node(shapes):
    found = False
    for ps in _property_shapes_for_path(shapes, DPC.performance):
        found = True
        assert (ps, SH["class"], SCHEMA.Observation) in shapes, "dpc:performance must use sh:class schema:Observation"
        assert not list(shapes.objects(ps, SH.node)), "dpc:performance must not use sh:node (to avoid recursion)"
    assert found, "No property shape found for dpc:performance"


def test_observationAbout_uses_class_not_node(shapes):
    found = False
    for ps in _property_shapes_for_path(shapes, SCHEMA.observationAbout):
        found = True
        assert (ps, SH["class"], DPC.HardwareComponent) in shapes, "schema:observationAbout must use sh:class dpc:HardwareComponent"
        assert not list(shapes.objects(ps, SH.node)), "schema:observationAbout must not use sh:node (to avoid recursion)"
    assert found, "No property shape found for schema:observationAbout"


def test_dsc_hasPart_uses_class_not_node(shapes):
    found = False
    for ps in _property_shapes_for_path(shapes, SCHEMA.hasPart):
        # Might be multiple property shapes using hasPart in all shapes
        if (ps, SH["class"], DPC.HardwareRuntime) in shapes or list(shapes.objects(ps, SH.node)):
            found = True
            assert (ps, SH["class"], DPC.HardwareRuntime) in shapes, "schema:hasPart for DistributedStep must use sh:class dpc:HardwareRuntime"
            assert not list(shapes.objects(ps, SH.node)), "schema:hasPart must not use sh:node (to avoid recursion)"
    assert found, "No property shape found for schema:hasPart -> dpc:HardwareRuntime"
