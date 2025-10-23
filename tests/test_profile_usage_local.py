from pyld import jsonld


def test_profile_context_roundtrip_local(server_base):
    """Test that the profile context works for JSON-LD expansion/compaction."""
    # Use only the profile context served by the local dev server
    ctx = f"{server_base}/contexts/lp-dscdpc/v1.jsonld"
    doc = {
        "@context": ctx,
        "@type": "DistributedStep",
        "used": "http://example.org/in",
        "generated": "http://example.org/out"
    }
    expanded = jsonld.expand(doc)
    assert expanded and isinstance(expanded, list)
    node = expanded[0]
    # Check a couple of expansions
    assert "https://livepublication.org/interface-schemas/dsc#DistributedStep" in node.get("@type", [])
    # Check PROV mappings exist
    assert "http://www.w3.org/ns/prov#used" in node
    assert node["http://www.w3.org/ns/prov#used"][0]["@id"] == "http://example.org/in"
    compacted = jsonld.compact(node, {"@context": ctx})
    assert compacted["@type"] == "DistributedStep"
    assert compacted["used"] == "http://example.org/in"
