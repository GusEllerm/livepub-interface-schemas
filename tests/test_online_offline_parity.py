"""
Online/offline parity verification.

Ensures ROCRATE_ONLINE=0/1 produce identical RDF output.
"""

import json
import os
import pathlib

import pytest
import rdflib as rdf

from tests._jsonld_utils import to_rdf_graph_from_jsonld


def _get_predicates(g: rdf.Graph) -> set:
    """Extract all predicates from graph."""
    return {str(p) for s, p, o in g.triples((None, None, None))}


def _get_classes(g: rdf.Graph) -> set:
    """Extract all classes from graph."""
    return {str(o) for s, p, o in g.triples((None, rdf.RDF.type, None))}


def _parse_with_rocrate_mode(crate_path: pathlib.Path, online: bool, server_base: str) -> rdf.Graph:
    """Parse crate with specific ROCRATE_ONLINE setting."""
    # Save and restore env var
    old_value = os.environ.get("ROCRATE_ONLINE")
    
    try:
        os.environ["ROCRATE_ONLINE"] = "1" if online else "0"
        
        # Re-import to pick up new env var
        import importlib
        import tests._jsonld_utils
        importlib.reload(tests._jsonld_utils)
        
        # Load and parse
        with open(crate_path, "r", encoding="utf-8") as fh:
            doc = json.load(fh)
        
        return tests._jsonld_utils.to_rdf_graph_from_jsonld(doc, server_base)
    
    finally:
        # Restore
        if old_value is None:
            os.environ.pop("ROCRATE_ONLINE", None)
        else:
            os.environ["ROCRATE_ONLINE"] = old_value
        
        # Reload again to restore
        import importlib
        import tests._jsonld_utils
        importlib.reload(tests._jsonld_utils)


def test_online_offline_parity(server_base, valid_crate_path):
    """
    Verify online and offline modes produce identical results.
    
    Checks:
    - Same triple count
    - Same predicate set
    - Same class set
    - File always expands to MediaObject (never schema:File)
    
    Note: RO-Crate 1.1 context uses http://schema.org, while our vendored
    contexts use https://schema.org. Normalized during comparison.
    
    This test is parametrized over all files in tests/crates/valid/
    via the valid_crate_path fixture from conftest.py.
    """
    g_online = _parse_with_rocrate_mode(valid_crate_path, True, server_base)
    g_offline = _parse_with_rocrate_mode(valid_crate_path, False, server_base)
    
    # Triple counts
    count_online = len(g_online)
    count_offline = len(g_offline)
    assert count_online == count_offline, (
        f"[{valid_crate_path.name}] Triple counts differ: online={count_online}, offline={count_offline}"
    )
    
    # Predicates
    predicates_online = _get_predicates(g_online)
    predicates_offline = _get_predicates(g_offline)
    
    # Normalize schema.org http/https differences
    predicates_online_norm = _normalize_schema_org_uris(predicates_online)
    predicates_offline_norm = _normalize_schema_org_uris(predicates_offline)
    
    if predicates_online_norm != predicates_offline_norm:
        only_online = predicates_online_norm - predicates_offline_norm
        only_offline = predicates_offline_norm - predicates_online_norm
        pytest.fail(
            f"[{valid_crate_path.name}] Predicate sets differ:\n"
            f"  Only in online: {only_online}\n"
            f"  Only in offline: {only_offline}"
        )
    
    # Classes
    classes_online = _get_classes(g_online)
    classes_offline = _get_classes(g_offline)
    
    # Normalize schema.org http/https differences
    classes_online_norm = _normalize_schema_org_uris(classes_online)
    classes_offline_norm = _normalize_schema_org_uris(classes_offline)
    
    if classes_online_norm != classes_offline_norm:
        only_online = classes_online_norm - classes_offline_norm
        only_offline = classes_offline_norm - classes_online_norm
        pytest.fail(
            f"[{valid_crate_path.name}] Class sets differ:\n"
            f"  Only in online: {only_online}\n"
            f"  Only in offline: {only_offline}"
        )
    
    # Verify File→MediaObject mapping enforced (regression guard)
    SCHEMA = "https://schema.org/"
    media_obj = SCHEMA + "MediaObject"
    schema_file = SCHEMA + "File"
    
    # MediaObject should be present (crate has File entity)
    assert media_obj in classes_online_norm, (
        f"[{valid_crate_path.name}] Expected MediaObject in online classes, got: {classes_online_norm}"
    )
    assert media_obj in classes_offline_norm, (
        f"[{valid_crate_path.name}] Expected MediaObject in offline classes, got: {classes_offline_norm}"
    )
    
    # schema:File should NEVER appear (File always maps to MediaObject)
    assert schema_file not in classes_online_norm, (
        f"[{valid_crate_path.name}] Unexpected schema:File in online classes (should be MediaObject)"
    )
    assert schema_file not in classes_offline_norm, (
        f"[{valid_crate_path.name}] Unexpected schema:File in offline classes (should be MediaObject)"
    )
    
    print(f"\n[{valid_crate_path.name}] ✓ Online/offline parity: {count_online} triples, "
          f"{len(predicates_online_norm)} predicates, {len(classes_online_norm)} classes")
    print(f"[{valid_crate_path.name}] ✓ File→MediaObject mapping enforced in both modes")



def _normalize_schema_org_uris(uris: set) -> set:
    """Normalize schema.org URIs to https for comparison."""
    return {
        uri.replace("http://schema.org/", "https://schema.org/")
        for uri in uris
    }
