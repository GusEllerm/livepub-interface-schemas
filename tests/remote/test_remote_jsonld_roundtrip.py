import os, pytest
from pyld import jsonld

BASE_URL = os.environ.get("BASE_URL")
pytestmark = pytest.mark.skipif(not BASE_URL, reason="Set BASE_URL to run remote tests")


def test_remote_jsonld_roundtrip():
    ctx = f"{BASE_URL}/dpc/contexts/v1.jsonld"
    sample = {
        "@context": ctx,
        "@type": "HardwareRuntime",
        "component": "http://example.org/run/123#gpu0"
    }

    expanded = jsonld.expand(sample)
    assert expanded and isinstance(expanded, list)
    node = expanded[0]

    comp_iri = "https://livepublication.org/interface-schemas/dpc#component"
    assert comp_iri in node
    assert node[comp_iri][0]["@id"] == "http://example.org/run/123#gpu0"

    compacted = jsonld.compact(node, {"@context": ctx})
    assert compacted["@type"] == "HardwareRuntime"
    assert compacted["component"] == "http://example.org/run/123#gpu0"
