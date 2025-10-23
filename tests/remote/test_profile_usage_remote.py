import os
import pytest
from pyld import jsonld

BASE_URL = os.environ.get("BASE_URL")
pytestmark = pytest.mark.skipif(not BASE_URL, reason="Set BASE_URL to run remote tests")


def test_profile_context_roundtrip_remote():
    """Test that the deployed profile context works for JSON-LD expansion/compaction."""
    ctx = f"{BASE_URL}/contexts/lp-dscdpc/v1.jsonld"
    doc = {
        "@context": ctx,
        "@type": "DistributedStep",
        "used": "http://example.org/in",
        "generated": "http://example.org/out"
    }
    expanded = jsonld.expand(doc)
    assert expanded and isinstance(expanded, list)
    node = expanded[0]
    assert "https://livepublication.org/interface-schemas/dsc#DistributedStep" in node.get("@type", [])
    assert "http://www.w3.org/ns/prov#generated" in node
    compacted = jsonld.compact(node, {"@context": ctx})
    assert compacted["@type"] == "DistributedStep"
    assert compacted["generated"] == "http://example.org/out"
