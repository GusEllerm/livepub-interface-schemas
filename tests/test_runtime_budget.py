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


BUDGET_SECONDS = 1.5


@pytest.mark.slow
def test_parse_runtime_budget(server_base, valid_crate_path):
    """
    Ensure single crate parse completes within budget.
    
    Skip on CI via SKIP_SLOW=1 environment variable.
    
    This test is parametrized over all files in tests/crates/valid/
    via the valid_crate_path fixture from conftest.py.
    """
    if os.environ.get("SKIP_SLOW") == "1":
        pytest.skip("SKIP_SLOW=1 set, skipping slow tests")
    
    with open(valid_crate_path, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    
    start = time.perf_counter()
    g = to_rdf_graph_from_jsonld(doc, server_base)
    elapsed = time.perf_counter() - start
    
    assert elapsed < BUDGET_SECONDS, (
        f"[{valid_crate_path.name}] Parse took {elapsed:.2f}s, exceeds budget of {BUDGET_SECONDS}s"
    )
    
    print(f"\n[{valid_crate_path.name}] ✓ Parse runtime: {elapsed:.3f}s (budget: {BUDGET_SECONDS}s)")
