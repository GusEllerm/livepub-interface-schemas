"""
Vocabulary baseline drift detection.

Compares current vocab inventory against a committed baseline
to catch unexpected vocabulary drift over time.
"""

import json
import os
import pathlib
from typing import Dict, List, Tuple, Any

import pytest


BASELINE_PATH = pathlib.Path(__file__).parent / "fixtures" / "vocab_baseline.json"
CURRENT_PATH = pathlib.Path(".artifacts") / "vocab_inventory.json"

# Tolerance for count changes (percent)
TOLERANCE_PERCENT = 20

# Critical terms that should not disappear or change dramatically
CRITICAL_TERMS = {
    "https://schema.org/object",
    "https://schema.org/result",
    "https://schema.org/hasPart",
    "https://schema.org/name",
    "https://schema.org/value",
    "https://schema.org/additionalProperty",
}


def _load_inventory(path: pathlib.Path) -> Dict[str, Any]:
    """Load vocabulary inventory JSON."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _dict_from_list(items: List[Tuple[str, int]]) -> Dict[str, int]:
    """Convert list of (key, count) tuples to dict."""
    return dict(items)


def _compare_namespaces(baseline: Dict[str, int], current: Dict[str, int]) -> List[str]:
    """
    Compare namespace counts.
    
    Returns list of drift messages.
    """
    messages = []
    
    # New namespaces
    new_ns = set(current.keys()) - set(baseline.keys())
    if new_ns:
        messages.append(f"NEW namespaces appeared: {sorted(new_ns)}")
    
    # Disappeared namespaces
    disappeared_ns = set(baseline.keys()) - set(current.keys())
    if disappeared_ns:
        messages.append(f"Namespaces DISAPPEARED: {sorted(disappeared_ns)}")
    
    # Significant count changes
    for ns in set(baseline.keys()) & set(current.keys()):
        base_count = baseline[ns]
        curr_count = current[ns]
        
        if base_count == 0:
            continue
        
        pct_change = abs((curr_count - base_count) / base_count) * 100
        
        if pct_change > TOLERANCE_PERCENT:
            direction = "increased" if curr_count > base_count else "decreased"
            messages.append(
                f"{ns}: {direction} from {base_count} to {curr_count} "
                f"({pct_change:.1f}% change, tolerance: {TOLERANCE_PERCENT}%)"
            )
    
    return messages


def _compare_terms(baseline: Dict[str, int], current: Dict[str, int], critical_only: bool = False) -> List[str]:
    """
    Compare term counts.
    
    Returns list of drift messages.
    """
    messages = []
    
    terms_to_check = CRITICAL_TERMS if critical_only else set(baseline.keys()) | set(current.keys())
    
    for term in sorted(terms_to_check):
        base_count = baseline.get(term, 0)
        curr_count = current.get(term, 0)
        
        if base_count == 0 and curr_count == 0:
            continue
        
        if base_count == 0:
            messages.append(f"{term}: NEW (count: {curr_count})")
            continue
        
        if curr_count == 0:
            messages.append(f"{term}: DISAPPEARED (was: {base_count})")
            continue
        
        pct_change = abs((curr_count - base_count) / base_count) * 100
        
        if pct_change > TOLERANCE_PERCENT:
            direction = "increased" if curr_count > base_count else "decreased"
            messages.append(
                f"{term}: {direction} from {base_count} to {curr_count} "
                f"({pct_change:.1f}% change)"
            )
    
    return messages


def test_vocab_baseline_drift():
    """
    Detect vocabulary drift from committed baseline.
    
    Fails if:
    - New namespaces appear (not in allowlist)
    - http://schema.org/ reappears
    - Critical terms disappear or change significantly
    
    Set VOCAB_BASELINE_UPDATE=1 to update the baseline (requires manual review and commit).
    """
    # Check if we should update the baseline
    if os.getenv("VOCAB_BASELINE_UPDATE") == "1":
        if CURRENT_PATH.exists():
            import shutil
            shutil.copy(CURRENT_PATH, BASELINE_PATH)
            print(f"\n[BASELINE] Updated baseline: {BASELINE_PATH}")
            print("[BASELINE] Please review changes and commit the updated baseline.")
            pytest.skip("Baseline updated; re-run tests to validate.")
        else:
            pytest.skip(f"Current inventory not found at {CURRENT_PATH}")
    
    # Load inventories
    baseline = _load_inventory(BASELINE_PATH)
    current = _load_inventory(CURRENT_PATH)
    
    if not baseline:
        pytest.skip(f"Baseline not found at {BASELINE_PATH}")
    
    if not current:
        pytest.fail(f"Current inventory not found at {CURRENT_PATH}. Run: make audit-vocab")
    
    # Compare
    issues = []
    
    # 1. Check for http://schema.org/ reappearance
    if current.get("http_schema_terms"):
        issues.append(f"HTTP schema.org terms REAPPEARED: {current['http_schema_terms']}")
    
    # 2. Check namespaces
    baseline_ns = _dict_from_list(baseline.get("by_namespace", []))
    current_ns = _dict_from_list(current.get("by_namespace", []))
    
    ns_drift = _compare_namespaces(baseline_ns, current_ns)
    if ns_drift:
        issues.append("NAMESPACE DRIFT:")
        issues.extend(f"  - {msg}" for msg in ns_drift)
    
    # 3. Check critical terms only (to avoid noise)
    baseline_terms = _dict_from_list(baseline.get("by_term", []))
    current_terms = _dict_from_list(current.get("by_term", []))
    
    term_drift = _compare_terms(baseline_terms, current_terms, critical_only=True)
    if term_drift:
        issues.append("CRITICAL TERM DRIFT:")
        issues.extend(f"  - {msg}" for msg in term_drift)
    
    # 4. Check for unknown namespaces
    if current.get("unknown_namespaces"):
        issues.append(f"UNKNOWN namespaces: {current['unknown_namespaces']}")
    
    # Report
    if issues:
        msg = ["\n[VOCAB BASELINE] Vocabulary drift detected:\n"]
        msg.extend(issues)
        msg.append("\nTo accept these changes, run:")
        msg.append("  VOCAB_BASELINE_UPDATE=1 pytest tests/test_vocab_baseline.py")
        msg.append("Then review and commit tests/fixtures/vocab_baseline.json")
        
        pytest.fail("\n".join(msg))
    
    print("\n[VOCAB BASELINE] ✓ No significant vocabulary drift detected")
