# LivePublication Interface Schemas (local dev)

## Run dev server
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
./serve_dev.py --root . --port 8000
```

Visit:
- http://localhost:8000/interface-schemas/dpc/contexts/v1.jsonld
- http://localhost:8000/interface-schemas/dpc/terms.ttl
- http://localhost:8000/interface-schemas/dpc/shapes.ttl

## Run tests (in another shell)
```bash
source .venv/bin/activate
python tests/test_jsonld_expand.py
python tests/test_shacl.py
```

## Commit
```bash
git add .
git -c user.name="REPLACE_WITH_YOUR_NAME" -c user.email="devnull@example.com" commit -m "feat: local skeleton for DPC/DSC with contexts, TTL, SHACL, dev server, tests"
```
