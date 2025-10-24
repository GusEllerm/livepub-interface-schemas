"""Guard test: ensure no examples remain in legacy tests/test_json/ directory."""
import glob
import os
import pytest

LEGACY_DIR = "tests/test_json"


def test_no_examples_in_legacy_dir():
    """
    Fail if any *.json files exist under tests/test_json/.
    
    All examples must be in tests/crates/valid/ or tests/crates/invalid/.
    """
    if not os.path.isdir(LEGACY_DIR):
        # Directory doesn't exist - that's fine
        return
    
    leftovers = sorted(glob.glob(f"{LEGACY_DIR}/**/*.json", recursive=True))
    assert not leftovers, (
        f"Found {len(leftovers)} JSON file(s) in legacy {LEGACY_DIR}/. "
        f"Move them to tests/crates/{{valid,invalid}}/. "
        f"Files: {leftovers}"
    )
