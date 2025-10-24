import glob
from rdflib import Dataset
from pyld import jsonld
from _jsonld_utils import make_requests_loader

EXAMPLES = sorted(glob.glob("tests/test_json/**/*.json", recursive=True)) + sorted(glob.glob("tests/test_json/*.json"))


def test_examples_produce_no_named_graphs(server_base):
    """Fail if any example produces quads in a non-default graph."""
    loader = make_requests_loader(server_base)
    for path in EXAMPLES:
        with open(path, "r", encoding="utf-8") as f:
            doc = __import__("json").load(f)
        nq = jsonld.to_rdf(doc, options={
            "documentLoader": loader,
            "format": "application/n-quads",
            "useNativeTypes": True,
            "produceGeneralizedRdf": False,
        })
        ds = Dataset()
        ds.parse(data=nq, format="nquads")
        for s, p, o, ng in ds.quads((None, None, None, None)):
            if ng is not None and ng != ds.default_context.identifier:
                raise AssertionError(f"Named graph detected in {path}: {ng}")
