#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
from pyld import jsonld
from tests._jsonld_utils import make_requests_loader

def main():
    if len(sys.argv) != 2:
        print("Usage: dump_nquads.py FILE", file=sys.stderr)
        sys.exit(2)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(2)
    server_base = os.environ.get("BASE_URL", "http://localhost:8000/interface-schemas")
    doc = json.loads(path.read_text(encoding="utf-8"))
    nq = jsonld.to_rdf(doc, options={
        "documentLoader": make_requests_loader(server_base),
        "format": "application/n-quads",
        "useNativeTypes": True,
        "produceGeneralizedRdf": False,
    })
    print(nq)

if __name__ == "__main__":
    main()
