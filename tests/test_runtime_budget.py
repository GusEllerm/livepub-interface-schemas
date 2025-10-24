"""
Runtime budget sanity checks.

Optional performance guard rails for CI.
"""

import json
import os
import pathlib
import time

import pytest

from tests._jsonld_utils import to_rdf_graph_from_jsonld


SMALL_CRATE = pathlib.Path("tests/crates/valid/dsc_min.json")
BUDGET_SECONDS = 1.5


@pytest.mark.slow
def test_parse_runtime_budget(server_base):
    """
    Ensure single crate parse completes within budget.
    
    Skip on CI via SKIP_SLOW=1 environment variable.
    """
    if os.environ.get("SKIP_SLOW") == "1":
        pytest.skip("SKIP_SLOW=1 set, skipping slow tests")
    
    with open(SMALL_CRATE, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    
    start = time.perf_counter()
    g = to_rdf_graph_from_jsonld(doc, server_base)
    elapsed = time.perf_counter() - start
    
    assert elapsed < BUDGET_SECONDS, (
        f"Parse took {elapsed:.2f}s, exceeds budget of {BUDGET_SECONDS}s"
    )
    
    print(f"\n✓ Parse runtime: {elapsed:.3f}s (budget: {BUDGET_SECONDS}s)")
