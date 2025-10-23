import os, pytest, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = os.environ.get("BASE_URL")
pytestmark = pytest.mark.skipif(not BASE_URL, reason="Set BASE_URL to run remote tests")


@pytest.mark.parametrize("path", ["/", "/dpc/", "/dsc/"])
def test_remote_links(path):
    base = f"{BASE_URL}{path}"
    r = requests.get(base, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Convert relative/./ links into absolute URLs under BASE_URL
        target = urljoin(base, href)
        # Only check same-site links under the /interface-schemas/ base
        if target.startswith(BASE_URL):
            rr = requests.get(target, timeout=10)
            assert rr.status_code == 200, f"Broken link from {base} → {href} ({target})"
