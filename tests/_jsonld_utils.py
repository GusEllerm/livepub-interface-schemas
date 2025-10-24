import json, os, requests
from pyld import jsonld
from rdflib import Dataset, Graph

LIVE_BASE = "https://livepublication.org/interface-schemas"

# Online by default (fetch RO-Crate contexts from w3id). Set ROCRATE_ONLINE=0 to force offline vendor copies.
ROCRATE_ONLINE = os.getenv("ROCRATE_ONLINE", "1") != "0"

# Allowlist for online fetch
ROCRATE_ALLOWED = {
    "https://w3id.org/ro/crate/1.1/context",
    "https://w3id.org/ro/terms/workflow-run/context",
}


def make_requests_loader(base_override: str):
    """
    Custom documentLoader:
    - Rewrites LIVE_BASE to base_override (local server or BASE_URL).
    - For RO-Crate contexts:
        * If ROCRATE_ONLINE=1 (default): fetch directly from the internet (allowlist).
        * If ROCRATE_ONLINE=0: rewrite to local vendor copies.
    - Blocks any other external URLs to keep tests deterministic.
    """

    # Local vendor fallbacks (used only when ROCRATE_ONLINE=0)
    VENDOR_MAP = {
        "https://w3id.org/ro/crate/1.1/context": f"{base_override}/vendor/ro-crate/1.1/context.jsonld",
        "https://w3id.org/ro/terms/workflow-run/context": f"{base_override}/vendor/ro-terms/workflow-run/context.jsonld",
    }

    cache = {}

    def loader(url, options=None):
        # 1) Rewrite your contexts to the local/remote base
        if url.startswith(LIVE_BASE):
            mapped = url.replace(LIVE_BASE, base_override, 1)

        # 2) RO-Crate contexts
        elif url in ROCRATE_ALLOWED:
            mapped = url if ROCRATE_ONLINE else VENDOR_MAP[url]

        # 2b) Allow direct fetches under the override base (localhost server or remote BASE_URL)
        elif base_override and url.startswith(base_override):
            mapped = url

        # 3) Block anything else
        else:
            raise RuntimeError(f"Blocked external context fetch: {url}")

        if mapped in cache:
            doc = cache[mapped]
        else:
            r = requests.get(mapped, timeout=15)  # requests follows redirects (w3id does 302s)
            r.raise_for_status()
            try:
                doc = r.json()
            except Exception as e:
                raise RuntimeError(f"Non-JSON from {mapped}") from e
            cache[mapped] = doc

        return {
            "contextUrl": None,
            "documentUrl": url,  # keep the original URL for provenance
            "document": doc,
        }

    return loader


def load_json_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def expand_with_override(doc: dict, base_override: str):
    loader = make_requests_loader(base_override)
    return jsonld.expand(doc, options={"documentLoader": loader})


def to_rdf_graph_from_jsonld(doc: dict, base_override: str, rdflib_graph=None):
    """
    Parse JSON-LD into an rdflib Dataset (avoids ConjunctiveGraph deprecation),
    then merge all quads into a plain Graph for SHACL validation.

    NOTE: This flattens named-graph boundaries. If we later need NG-aware logic,
    we'll keep the Dataset and adapt validation accordingly. Current shapes
    do not rely on named graphs, so this is safe.
    """
    # --- keep the existing @context rewrite logic (LIVE_BASE/ROCRATE_ONLINE) ---
    ctx = doc.get("@context")

    def rewrite_ctx_item(item):
        if isinstance(item, str):
            if item.startswith(LIVE_BASE):
                return item.replace(LIVE_BASE, base_override, 1)
            if not ROCRATE_ONLINE:
                if item == "https://w3id.org/ro/crate/1.1/context":
                    return f"{base_override}/vendor/ro-crate/1.1/context.jsonld"
                if item == "https://w3id.org/ro/terms/workflow-run/context":
                    return f"{base_override}/vendor/ro-terms/workflow-run/context.jsonld"
        return item

    if isinstance(ctx, list):
        doc["@context"] = [rewrite_ctx_item(c) for c in ctx]
    elif isinstance(ctx, str):
        doc["@context"] = rewrite_ctx_item(ctx)

    # Prefer avoiding rdflib's JSON-LD parser to eliminate ConjunctiveGraph warnings.
    # Use pyld to produce N-Quads, then load via rdflib's nquads parser.
    loader = make_requests_loader(base_override)
    expanded = jsonld.expand(doc, options={"documentLoader": loader})
    nquads = jsonld.to_rdf(expanded, options={"format": "application/n-quads"})

    g = Graph()
    g.parse(data=nquads, format="nquads")
    return g
