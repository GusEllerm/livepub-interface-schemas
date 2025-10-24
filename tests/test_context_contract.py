"""Contract tests for lp-dscdpc profile context expansion."""
import json
import pytest
from pyld import jsonld


PROFILE_PATH = "interface-schemas/contexts/lp-dscdpc/v1.jsonld"


def test_profile_preserves_schema_vocab():
    """The profile context must map 'name' to https://schema.org/name."""
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        profile = json.load(f)
    
    ctx = profile["@context"]
    
    # Check @vocab is set to schema.org
    assert ctx.get("@vocab") == "https://schema.org/", \
        "Profile must set @vocab to https://schema.org/"
    
    # Verify 'name' expands to schema:name using inline context
    test_doc = {
        "@context": ctx,
        "@id": "http://example.org/test",
        "name": "Test Name"
    }
    
    expanded = jsonld.expand(test_doc)
    assert len(expanded) == 1
    assert "https://schema.org/name" in expanded[0], \
        f"'name' should expand to https://schema.org/name, got: {list(expanded[0].keys())}"
    assert expanded[0]["https://schema.org/name"][0]["@value"] == "Test Name"


def test_profile_maps_dpc_and_dsc_terms():
    """The profile context must map DPC and DSC terms to expected IRIs."""
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        profile = json.load(f)
    
    ctx = profile["@context"]
    
    # Check namespace prefixes
    assert ctx.get("dpc") == "https://livepublication.org/interface-schemas/dpc#"
    assert ctx.get("dsc") == "https://livepublication.org/interface-schemas/dsc#"
    
    # Check type mappings
    assert ctx.get("HardwareRuntime") == "dpc:HardwareRuntime"
    assert ctx.get("HardwareComponent") == "dpc:HardwareComponent"
    assert ctx.get("DistributedStep") == "dsc:DistributedStep"
    
    # Verify expansion using inline context
    test_doc = {
        "@context": ctx,
        "@id": "http://example.org/test",
        "@type": ["DistributedStep", "HardwareRuntime"]
    }
    
    expanded = jsonld.expand(test_doc)
    assert len(expanded) == 1
    types = expanded[0]["@type"]
    assert "https://livepublication.org/interface-schemas/dsc#DistributedStep" in types
    assert "https://livepublication.org/interface-schemas/dpc#HardwareRuntime" in types


def test_profile_overrides_schema_terms_to_https():
    """Profile must map common schema terms (e.g., hasPart) to HTTPS IRIs.

    This ensures compatibility with shapes that use the https://schema.org/ namespace
    even when upstream contexts (like RO-Crate) may define http://schema.org/ terms.
    """
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        profile = json.load(f)

    ctx = profile["@context"]

    test_doc = {
        "@context": ctx,
        "@id": "http://example.org/step",
        "hasPart": {"@id": "http://example.org/runtime"}
    }

    expanded = jsonld.expand(test_doc)
    assert len(expanded) == 1
    keys = set(expanded[0].keys())
    assert "https://schema.org/hasPart" in keys, f"hasPart must expand to HTTPS schema.org IRI, got: {keys}"


def test_profile_maps_object_and_result_to_https():
    """Profile must map object and result to HTTPS schema.org IRIs.

    This ensures DSC I/O properties (object=input, result=output) expand correctly
    even when RO-Crate contexts may define them as http IRIs.
    """
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        profile = json.load(f)

    ctx = profile["@context"]

    test_doc = {
        "@context": ctx,
        "@id": "http://example.org/step",
        "object": {"@id": "http://example.org/input"},
        "result": {"@id": "http://example.org/output"}
    }

    expanded = jsonld.expand(test_doc)
    assert len(expanded) == 1
    keys = set(expanded[0].keys())
    assert "https://schema.org/object" in keys, f"object must expand to HTTPS schema.org IRI, got: {keys}"
    assert "https://schema.org/result" in keys, f"result must expand to HTTPS schema.org IRI, got: {keys}"
