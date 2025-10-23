import json, requests
from pyld import jsonld


doc = json.load(open("tests/sample_dpc.json"))
ctx_url = doc["@context"]

# Ensure local context is reachable
r = requests.get(ctx_url, timeout=5)
r.raise_for_status()

expanded = jsonld.expand(doc)
print("Expanded node count:", len(expanded))
assert len(expanded) >= 1
print("OK: JSON-LD expanded successfully.")
