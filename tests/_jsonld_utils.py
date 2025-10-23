import json, os, requests
from pyld import jsonld

LIVE_BASE = "https://livepublication.org/interface-schemas"


def make_requests_loader(base_override: str):
    """
    Create a pyld documentLoader that:
    - Rewrites LIVE_BASE to base_override (local or remote base).
    - Fetches using requests and returns JSON content for contexts/documents.
    - Never attempts other network calls unless the URL begins with LIVE_BASE.
      (Safety: reject non-LIVE_BASE URLs to avoid external fetches in local tests.)
    """
    def loader(url, options=None):
        if url.startswith(LIVE_BASE):
            mapped = url.replace(LIVE_BASE, base_override, 1)
        else:
            # Allow file: and http(s) ONLY if it's still under the override base.
            # For local tests we'll only see LIVE_BASE; for remote tests BASE_URL is used.
            if base_override and url.startswith(base_override):
                mapped = url
            else:
                raise RuntimeError(f"Blocked external context fetch: {url}")

        r = requests.get(mapped, timeout=10)
        r.raise_for_status()
        doc = r.json()
        return {
            "contextUrl": None,
            "documentUrl": url,   # keep original
            "document": doc
        }
    return loader


def load_json_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def expand_with_override(doc: dict, base_override: str):
    """
    Expand a JSON-LD document using a custom loader that rewrites LIVE_BASE to base_override.
    """
    loader = make_requests_loader(base_override)
    return jsonld.expand(doc, options={"documentLoader": loader})


def to_rdf_graph_from_jsonld(doc: dict, base_override: str, rdflib_graph):
    """
    Convert a JSON-LD doc to RDF using rdflib, after expansion via base_override.
    We compact back with the same context to keep bnodes stable-ish; rdflib parses JSON-LD directly.
    """
    # Use rdflib's JSON-LD parser; first ensure any embedded remote contexts are rewritten.
    # A simple approach is to replace LIVE_BASE -> base_override inside @context if it's a string or list of strings.
    ctx = doc.get("@context")
    if isinstance(ctx, str) and ctx.startswith(LIVE_BASE):
        doc["@context"] = ctx.replace(LIVE_BASE, base_override, 1)
    elif isinstance(ctx, list):
        new = []
        for c in ctx:
            if isinstance(c, str) and c.startswith(LIVE_BASE):
                new.append(c.replace(LIVE_BASE, base_override, 1))
            else:
                new.append(c)
        doc["@context"] = new

    rdflib_graph.parse(data=json.dumps(doc), format="json-ld")
    return rdflib_graph
