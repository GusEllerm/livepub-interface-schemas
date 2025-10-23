import os, pytest, requests

BASE_URL = os.environ.get("BASE_URL")  # e.g., https://livepublication.org/interface-schemas
pytestmark = pytest.mark.skipif(not BASE_URL, reason="Set BASE_URL to run remote tests")


def _url(p):  # ensure path starts with /
    return f"{BASE_URL}{p}"


@pytest.mark.parametrize("path,ctype,cache_required", [
    ("/contexts/lp-dscdpc/v1.jsonld", "application/ld+json", True),
    ("/dpc/contexts/v1.jsonld",  "application/ld+json", True),
    ("/dpc/terms.ttl",          "text/turtle",         False),
    ("/dpc/shapes.ttl",         "text/turtle",         False),
    ("/dsc/contexts/v1.jsonld", "application/ld+json", True),
    ("/dsc/terms.ttl",          "text/turtle",         False),
    ("/dsc/shapes.ttl",         "text/turtle",         False),
    ("/dpc/",                   "text/html",           False),
    ("/dsc/",                   "text/html",           False),
    ("/",                       "text/html",           False),
])
def test_remote_headers(path, ctype, cache_required):
    url = _url(path)
    r = requests.get(url, timeout=10)
    assert r.status_code == 200, url
    ct = r.headers.get("Content-Type", "")
    assert ctype in ct, (url, ct)
    assert r.headers.get("Access-Control-Allow-Origin") == "*", f"CORS missing on {url}"
    cc = r.headers.get("Cache-Control", "")
    if cache_required:
        assert "immutable" in cc and "max-age=" in cc, f"Cache header issue on {url}"
