import pytest
from rdflib import Graph, Literal, Namespace
from _jsonld_utils import to_rdf_graph_from_jsonld, make_requests_loader

SCHEMA = Namespace("https://schema.org/")


def test_schema_value_is_typed_number(server_base):
    # Minimal observation with numeric value
    doc = {
        "@context": [
          "https://w3id.org/ro/crate/1.1/context",
          "https://w3id.org/ro/terms/workflow-run/context",
          f"{server_base}/contexts/lp-dscdpc/v1.jsonld"
        ],
        "@type": "Observation",
        "value": 0.0
    }
    g = to_rdf_graph_from_jsonld(doc, base_override=server_base)
    # Collect all literals and ensure at least one numeric typed literal is present
    vals = [o for _,_,o in g if isinstance(o, Literal)]
    assert vals, "No literals found in graph"
    assert any(o.datatype and ("double" in str(o.datatype) or "integer" in str(o.datatype)) for o in vals), \
        f"Expected numeric typed literal, got: {vals!r}"


def test_loader_blocks_unexpected_external(server_base):
    loader = make_requests_loader(server_base)
    with pytest.raises(RuntimeError):
        loader("https://not-allowed.example/context.jsonld")


def test_loader_allows_base_override_only_if_prefix_match(server_base):
    loader = make_requests_loader(server_base)
    u = f"{server_base}/dpc/contexts/v1.jsonld"
    # Should not raise for allowed base URL
    loader(u)


def test_loader_rejects_wrong_scheme(server_base):
    bad_base = server_base.replace("http", "ftp")
    loader = make_requests_loader(bad_base)
    with pytest.raises(RuntimeError):
        loader("ftp://example.org/anything.jsonld")
