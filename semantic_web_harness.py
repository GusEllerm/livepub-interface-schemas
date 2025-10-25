#!/usr/bin/env python3
"""
semantic_web_harness.py

Goal:
- Load one of our example crates (JSON-LD from tests/crates/valid/)
- Resolve its remote @context URLs exactly like a consumer on the public web
  (including w3id.org and livepublication.org)
- Expand to RDF with pyld
- Serialize to N-Quads
- Inspect:
  - predicates
  - classes (rdf:type targets)
  - use of our livepublication.org terms
  - http://schema.org/* leaks
  - any schema:File usage

This simulates "how the semantic web sees us".
"""

import json
import re
import collections
import requests
from pyld import jsonld

# ---------------------------------------------------------------------
# 1. Pick which crate to analyze
#    You can swap this to any file under tests/crates/valid/
# ---------------------------------------------------------------------
CRATE_PATH = "/Users/eller/Projects/interface-schema/tests/crates/valid/dsc_full_01.json"

# How many N-Quads lines to preview in output
PREVIEW_LINES = 30


# ---------------------------------------------------------------------
# 2. Custom remote document loader for pyld
#
# pyld will call this as:
#   loader(url)
# or
#   loader(url, options)
#
# We must accept that 2nd arg even if we don't use it.
#
# We also:
# - print what we're fetching
# - follow redirects (requests does that by default)
# - prefer JSON-LD in Accept header
# - return the JSON body and the final URL
# ---------------------------------------------------------------------
def custom_document_loader(url, options=None):
    print(f"[fetch] {url}")
    headers = {
        "Accept": "application/ld+json, application/json;q=0.9, */*;q=0.1"
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()

    # requests follows redirects, so resp.url is the final URL
    final_url = resp.url

    # Assume it's JSON(-LD). If it's not, this will raise, which is fine.
    doc = resp.json()

    return {
        "contextUrl": None,
        "documentUrl": final_url,
        "document": doc,
    }


# Tell pyld to use our loader for everything (contexts, etc.)
jsonld.set_document_loader(custom_document_loader)


# ---------------------------------------------------------------------
# 3. Load crate JSON-LD from disk
# ---------------------------------------------------------------------
with open(CRATE_PATH, "r", encoding="utf-8") as f:
    crate = json.load(f)

# ---------------------------------------------------------------------
# 4. Expand with pyld (fully qualified IRIs)
# ---------------------------------------------------------------------
expanded = jsonld.expand(crate)

print(expanded)

# ---------------------------------------------------------------------
# 5. Convert to RDF (N-Quads)
# ---------------------------------------------------------------------
nquads = jsonld.to_rdf(expanded, options={"format": "application/n-quads"})


# ---------------------------------------------------------------------
# 6. Parse N-Quads so we can count predicates and classes
# ---------------------------------------------------------------------

predicate_counter = collections.Counter()
class_counter = collections.Counter()

# naive N-Quads triple regex:
# <subj> <pred> <obj> .
# subj can be <IRI> or _:bnode
# obj can be <IRI>, _:bnode, or "literal"^^<dt> / "literal"@lang
TRIPLE_RE = re.compile(
    r'^(?P<s>\S+)\s+(?P<p>\S+)\s+(?P<o>.+?)\s+\.\s*$'
)

RDF_TYPE = "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"

livepub_terms = set()         # IRIs under https://livepublication.org/interface-schemas/
http_schema_terms = set()     # anything starting http://schema.org/
saw_schema_file_class = False # did anything get rdf:type schema:File ?

for line in nquads.splitlines():
    m = TRIPLE_RE.match(line)
    if not m:
        continue

    s = m.group("s")
    p = m.group("p")
    o = m.group("o")

    # normalize <...> form to a bare IRI string when possible
    def strip_angle(v):
        return v[1:-1] if v.startswith("<") and v.endswith(">") else v

    subj_iri = strip_angle(s)
    pred_iri = strip_angle(p)
    obj_val = o.strip()

    # Count predicates
    predicate_counter[pred_iri] += 1

    # If rdf:type, then object is a class IRI (when it's an IRI)
    if p == RDF_TYPE:
        # Only count if object is an IRI, not literal or blank node
        if obj_val.startswith("<") and obj_val.endswith(">"):
            class_iri = strip_angle(obj_val)
            class_counter[class_iri] += 1
            # guard for schema:File
            no_slash = class_iri.rstrip("/")
            if no_slash in (
                "http://schema.org/File",
                "https://schema.org/File",
            ):
                saw_schema_file_class = True

    # Track our own namespace terms
    if pred_iri.startswith("https://livepublication.org/interface-schemas/"):
        livepub_terms.add(pred_iri)
    if obj_val.startswith("<https://livepublication.org/interface-schemas/"):
        livepub_terms.add(strip_angle(obj_val))

    # Track any http://schema.org usage (http, not https)
    if pred_iri.startswith("http://schema.org/"):
        http_schema_terms.add(pred_iri)
    if obj_val.startswith("<http://schema.org/"):
        http_schema_terms.add(strip_angle(obj_val))


# ---------------------------------------------------------------------
# 7. Pretty-print diagnostics
# ---------------------------------------------------------------------

print()
print(f"=== N-Quads Preview (first {PREVIEW_LINES} lines) ===")
preview_lines = nquads.splitlines()[:PREVIEW_LINES]
for pl in preview_lines:
    print(pl)
if len(nquads.splitlines()) > PREVIEW_LINES:
    print("...")

print()
print("=== Unique predicate IRIs (top 20) ===")
for iri, count in predicate_counter.most_common(20):
    print(f"{iri}  ({count} uses)")

print()
print("=== Unique class IRIs (top 20) ===")
if class_counter:
    for iri, count in class_counter.most_common(20):
        print(f"{iri}  ({count} uses)")
else:
    print("(none found – if this stays empty for crates that you KNOW declare "
          "types like schema:Dataset etc, something's off and we should inspect)")

print()
print("=== livepublication.org/interface-schemas/* terms observed ===")
if livepub_terms:
    for t in sorted(livepub_terms):
        print(t)
else:
    print("(none)")

print()
print("=== http://schema.org/* terms observed (should be empty) ===")
if http_schema_terms:
    for t in sorted(http_schema_terms):
        print(t)
else:
    print("(none)")

print()
print("=== Checks ===")
print("No http://schema.org/* terms? {}".format(
    "YES" if not http_schema_terms else "NO"
))
print("No schema:File class (should be MediaObject instead)? {}".format(
    "YES" if not saw_schema_file_class else "NO"
))

print()
print("Done.")
