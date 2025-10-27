import glob
import json
import pytest
from rdflib import Namespace, URIRef
from _jsonld_utils import to_rdf_graph_from_jsonld

VALID_CRATES = sorted(glob.glob("tests/crates/valid/*.json"))
ALL_CRATES = sorted(glob.glob("tests/crates/**/*.json", recursive=True))

PROFILE_CANONICAL = "https://livepublication.org/interface-schemas/contexts/lp-dscdpc/v1.jsonld"
PROFILE_W3ID = "https://w3id.org/livepublication/interface-schemas/contexts/lp-dscdpc/v1.jsonld"

DSC = Namespace("https://livepublication.org/interface-schemas/dsc#")
DPC = Namespace("https://livepublication.org/interface-schemas/dpc#")


@pytest.mark.parametrize("path", ALL_CRATES)
def test_examples_include_profile_context(path):
    """All crate examples must include the lp-dscdpc profile context."""
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    ctx = doc.get("@context", [])
    if isinstance(ctx, str):
        ctx = [ctx]
    assert PROFILE_CANONICAL in ctx or PROFILE_W3ID in ctx, \
        f"{path} is missing the profile context ({PROFILE_CANONICAL} or {PROFILE_W3ID})"


@pytest.mark.parametrize("path", VALID_CRATES)
def test_valid_crates_have_dsc_or_dpc_targets(server_base, path):
    """Valid crates must contain at least one DSC or DPC typed node."""
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    g = to_rdf_graph_from_jsonld(doc, base_override=server_base)
    
    # Get all rdf:type triples
    RDF_type = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
    types = set(o for s, p, o in g.triples((None, RDF_type, None)))
    
    # Check if any type starts with DSC or DPC namespace
    has_target = any(
        str(t).startswith(str(DSC)) or str(t).startswith(str(DPC)) 
        for t in types
    )
    
    assert has_target, (
        f"No dsc: or dpc: typed nodes found in {path}. "
        f"Found types: {[str(t) for t in types]}"
    )
