import json
import urllib.request
from pyld import jsonld

# Pick a representative valid crate that includes DistributedStep and DPC hardware info.
CRATE_PATH = "tests/crates/valid/dsc_full_02.json"

def fetch(url):
    print(f"[fetch] {url}")
    # Follow redirects automatically
    req = urllib.request.Request(url)
    req.add_header('Accept', 'application/ld+json, application/json')
    with urllib.request.urlopen(req) as r:
        # Get final URL after redirects
        final_url = r.geturl()
        content_type = r.headers.get('Content-Type', 'application/json')
        content = r.read().decode("utf-8")
        if final_url != url:
            print(f"  -> redirected to {final_url}")
        return content, final_url, content_type

def loader(url, _options=None):
    # Custom loader so pyld uses urllib and we can observe each fetch.
    doc, final_url, content_type = fetch(url)
    return {
        "contentType": content_type,
        "contextUrl": None,
        "documentUrl": final_url,  # Use final URL after redirects
        "document": doc,
    }

with open(CRATE_PATH, "r") as f:
    crate = json.load(f)

# Expand using public contexts only (w3id / livepublication.org)
expanded = jsonld.expand(
    crate,
    options={"documentLoader": loader}
)

print(f"\nExpanded graph has {len(expanded)} nodes\n")

# Collect class IRIs and predicate IRIs
all_types = []
pred_counts = {}

for node in expanded:
    for t in node.get("@type", []):
        all_types.append(t)
    for pred, vals in node.items():
        if pred in ("@id", "@type"):
            continue
        pred_counts[pred] = pred_counts.get(pred, 0) + len(vals)

print("Unique class IRIs:")
for iri in sorted(set(all_types)):
    print(" ", iri)

print("\nPredicates using livepublication.org/interface-schemas/:")
for p in sorted(k for k in pred_counts if k.startswith("https://livepublication.org/interface-schemas/")):
    print(" ", p)

http_schema_preds = sorted(k for k in pred_counts if k.startswith("http://schema.org/"))
print("\nAny http://schema.org/* predicates?")
print(" ", "NO" if not http_schema_preds else "YES: " + ", ".join(http_schema_preds))

bad_file_class = any(t.endswith("/File") for t in all_types if "schema.org" in t)
print("\nAny schema:File class types?")
print(" ", "NO" if not bad_file_class else "YES (should be MediaObject)")
