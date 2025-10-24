"""Centralized discovery for JSON-LD example crates."""
import glob
from typing import List

CRATES_VALID_DIR = "tests/crates/valid"
CRATES_INVALID_DIR = "tests/crates/invalid"


def list_all_examples() -> List[str]:
    """Return all JSON example files (valid + invalid)."""
    return sorted(
        glob.glob(f"{CRATES_VALID_DIR}/**/*.json", recursive=True) +
        glob.glob(f"{CRATES_INVALID_DIR}/**/*.json", recursive=True)
    )


def list_valid_examples() -> List[str]:
    """Return all valid JSON example files."""
    return sorted(glob.glob(f"{CRATES_VALID_DIR}/**/*.json", recursive=True))


def list_invalid_examples() -> List[str]:
    """Return all invalid JSON example files."""
    return sorted(glob.glob(f"{CRATES_INVALID_DIR}/**/*.json", recursive=True))
