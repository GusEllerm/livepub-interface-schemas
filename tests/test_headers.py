import requests
import pytest


@pytest.mark.parametrize("path,ctype,cache_required", [
    ("/contexts/lp-dscdpc/v1.jsonld", "application/ld+json", True),
    ("/dpc/contexts/v1.jsonld", "application/ld+json", True),
    ("/dpc/terms.ttl",         "text/turtle",         False),
    ("/dpc/shapes.ttl",        "text/turtle",         False),
    ("/dsc/contexts/v1.jsonld", "application/ld+json", True),
    ("/dsc/terms.ttl",          "text/turtle",         False),
    ("/dsc/shapes.ttl",         "text/turtle",         False),
    ("/dpc/",                   "text/html",           False),
    ("/dsc/",                   "text/html",           False),
    ("/",                       "text/html",           False),
])
def test_headers(server_base, path, ctype, cache_required):
    url = f"{server_base}{path}"
    r = requests.get(url, timeout=5)
    assert r.status_code == 200, url
    # Content-Type (allow possible charset suffix for HTML)
    ct = r.headers.get("Content-Type","")
    assert ctype in ct, (url, ct)
    # CORS must be present for all (esp. JSON-LD contexts)
    assert r.headers.get("Access-Control-Allow-Origin") == "*"
    # Cache header required only for versioned contexts
    cc = r.headers.get("Cache-Control","")
    if cache_required:
        assert "immutable" in cc and "max-age=" in cc
