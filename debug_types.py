#!/usr/bin/env python3
"""Debug script to inspect types in dpc_min.json"""
import json
import sys
sys.path.insert(0, 'tests')
from _jsonld_utils import to_rdf_graph_from_jsonld
from rdflib import RDF

with open('tests/crates/valid/dpc_min.json') as f:
    data = json.load(f)

g = to_rdf_graph_from_jsonld(data, base_override='http://localhost:8000/interface-schemas')

print("All triples:")
for s, p, o in g:
    print(f"  {s} {p} {o}")

print("\nAll rdf:type triples:")
for s, p, o in g.triples((None, RDF.type, None)):
    print(f"  {s} -> {o}")

print(f"\nTotal triples: {len(g)}")
