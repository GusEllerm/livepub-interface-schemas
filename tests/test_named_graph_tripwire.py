import json
from rdflib import Dataset
from pyld import jsonld
from _jsonld_utils import make_requests_loader
from _example_loader import list_all_examples


def test_examples_produce_no_named_graphs(server_base):
    """Fail if any example produces quads in a non-default graph."""
    loader = make_requests_loader(server_base)
    for path in list_all_examples():
        with open(path, "r", encoding="utf-8") as f:
            doc = json.load(f)
        nq = jsonld.to_rdf(doc, options={
            "documentLoader": loader,
            "format": "application/n-quads",
            "useNativeTypes": True,
            "produceGeneralizedRdf": False,
            "base": server_base
        })
        ds = Dataset()
        ds.parse(data=nq, format="nquads")
        for s, p, o, ng in ds.quads((None, None, None, None)):
            if ng is not None and ng != ds.default_context.identifier:
                raise AssertionError(f"Named graph detected in {path}: {ng}")
