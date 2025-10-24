"""
Test fixture layout enforcement.

Ensures all JSON-LD test crates are in tests/crates/{valid,invalid}/.
"""

import pathlib


def test_no_stray_json_files():
    """
    Fail if JSON/JSON-LD files exist outside tests/crates/{valid,invalid}/.
    
    This prevents test fixture sprawl and ensures consistent organization.
    """
    tests_dir = pathlib.Path("tests")
    allowed_dirs = {
        tests_dir / "crates" / "valid",
        tests_dir / "crates" / "invalid",
    }
    
    violations = []
    
    # Walk all of tests/ recursively
    for path in tests_dir.rglob("*.json"):
        # Check if path is under any allowed dir
        is_allowed = any(
            _is_subpath(path, allowed) for allowed in allowed_dirs
        )
        
        if not is_allowed:
            # Also allow tests/fixtures/ for baselines
            if path.parent == tests_dir / "fixtures":
                continue
            violations.append(path)
    
    # Also check .jsonld files
    for path in tests_dir.rglob("*.jsonld"):
        is_allowed = any(
            _is_subpath(path, allowed) for allowed in allowed_dirs
        )
        
        if not is_allowed:
            violations.append(path)
    
    if violations:
        msg = [
            "Found JSON/JSON-LD files outside tests/crates/{valid,invalid}/:",
            "",
        ]
        for v in violations:
            msg.append(f"  {v}")
        
        msg.extend([
            "",
            "Remediation:",
            "  Move these files to:",
            "    tests/crates/valid/    - for conforming crates",
            "    tests/crates/invalid/  - for non-conforming crates",
            "  Or delete if obsolete.",
        ])
        
        raise AssertionError("\n".join(msg))
    
    print(f"\n✓ Fixture layout clean: all crates in tests/crates/{{valid,invalid}}/")


def _is_subpath(path: pathlib.Path, parent: pathlib.Path) -> bool:
    """Check if path is under parent directory."""
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False
