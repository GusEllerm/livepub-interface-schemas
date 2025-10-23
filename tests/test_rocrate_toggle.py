import os
from rdflib import Graph
from _jsonld_utils import expand_with_override, to_rdf_graph_from_jsonld


def test_rocrate_online_default(server_base, monkeypatch):
    # Ensure default is online; no need to set env var
    doc = {"@context": [
        "https://w3id.org/ro/crate/1.1/context",
        "https://w3id.org/ro/terms/workflow-run/context"
    ], "@type": "Dataset", "name": "ok"}
    expanded = expand_with_override(doc, server_base)
    assert expanded


def test_rocrate_offline_vendor(server_base, monkeypatch):
    # Force offline mode; should use vendor copies served locally
    monkeypatch.setenv("ROCRATE_ONLINE", "0")
    doc = {"@context": [
        "https://w3id.org/ro/crate/1.1/context",
        "https://w3id.org/ro/terms/workflow-run/context"
    ], "@type": "Dataset", "name": "ok"}
    g = Graph()
    to_rdf_graph_from_jsonld(doc, server_base, g)
    assert len(g) >= 1
