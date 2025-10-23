import json, requests
from pyld import jsonld


def test_expand_compact(server_base):
    ctx_url = f"{server_base}/dpc/contexts/v1.jsonld"
    sample = {
        "@context": ctx_url,
        "@type": "HardwareRuntime",
        "component": "http://example.org/run/123#gpu0"
    }

    # Expand
    expanded = jsonld.expand(sample)
    assert expanded and isinstance(expanded, list)
    node = expanded[0]

    # Verify type expanded to the full IRI
    types = node.get("@type", [])
    assert "https://livepublication.org/interface-schemas/dpc#HardwareRuntime" in types

    # Verify property expansion to IRI
    comp_iri = "https://livepublication.org/interface-schemas/dpc#component"
    assert comp_iri in node
    obj = node[comp_iri][0]
    assert obj.get("@id") == "http://example.org/run/123#gpu0"

    # Compact back and ensure we recover the compact keys
    ctx = requests.get(ctx_url, timeout=5).json()
    compacted = jsonld.compact(node, ctx["@context"])
    assert compacted.get("@type") == "HardwareRuntime"
    assert compacted.get("component") == "http://example.org/run/123#gpu0"
