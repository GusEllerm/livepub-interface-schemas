import requests
from bs4 import BeautifulSoup
import pytest


@pytest.mark.parametrize("path", ["/", "/dpc/", "/dsc/"])
def test_links_resolve(server_base, path):
    url = f"{server_base}{path}"
    r = requests.get(url, timeout=5)
    assert r.ok
    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Make relative hrefs absolute under /interface-schemas
        if href.startswith("./"):
            href = path + href[2:]
        elif href.startswith("/interface-schemas/"):
            pass
        elif href.startswith("/"):
            # Treat as site-absolute under interface-schemas
            href = f"/interface-schemas{href}"
        # Otherwise skip external
        else:
            continue
        rr = requests.get(f"{server_base}{href.removeprefix('/interface-schemas')}", timeout=5)
        assert rr.status_code == 200, f"Broken link from {url} -> {href}"
