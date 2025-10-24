"""
Make target dry-run verification.

Ensures documented Make targets execute without errors.
"""

import pathlib
import re
import subprocess


def test_make_targets_dry_run():
    """
    Verify Make targets with dry-run (-n).
    
    Checks that targets are defined and reference expected modules.
    """
    targets = [
        ("test-online", r"ROCRATE_ONLINE=1.*pytest"),
        ("test-offline", r"ROCRATE_ONLINE=0.*pytest"),
        ("audit-vocab", r"tests/test_vocab_audit\.py"),
        ("audit-sparql", r"tests/policy/test_vocab_sparql\.py"),
        ("audit-shapes", r"tests/test_shapes_coverage\.py"),
    ]
    
    # Discover a valid crate file for debug-nq test
    valid_dir = pathlib.Path("tests/crates/valid")
    valid_crates = sorted(valid_dir.glob("*.json")) if valid_dir.exists() else []
    
    # Separate test for debug-nq (requires FILE= parameter)
    targets_with_args = []
    if valid_crates:
        # Use first valid crate found
        test_crate = valid_crates[0]
        targets_with_args = [
            ("debug-nq", f"FILE={test_crate}", r"tools/dump_nquads\.py"),
        ]
    else:
        print("\n[WARNING] No valid crates found, skipping debug-nq target test")
    
    failures = []
    
    for target, pattern in targets:
        try:
            result = subprocess.run(
                ["make", "-n", target],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
            
            # Verify pattern match
            if not re.search(pattern, result.stdout, re.MULTILINE):
                failures.append(
                    f"Target '{target}' output doesn't match pattern '{pattern}':\n"
                    f"{result.stdout}"
                )
        
        except subprocess.CalledProcessError as e:
            failures.append(
                f"Target '{target}' failed with exit code {e.returncode}:\n"
                f"stdout: {e.stdout}\n"
                f"stderr: {e.stderr}"
            )
        
        except subprocess.TimeoutExpired:
            failures.append(f"Target '{target}' timed out (>5s)")
    
    # Test targets that require arguments
    for target, arg, pattern in targets_with_args:
        try:
            result = subprocess.run(
                ["make", "-n", target, arg],
                capture_output=True,
                text=True,
                timeout=5,
                check=True,
            )
            
            # Verify pattern match
            if not re.search(pattern, result.stdout, re.MULTILINE):
                failures.append(
                    f"Target '{target}' output doesn't match pattern '{pattern}':\n"
                    f"{result.stdout}"
                )
        
        except subprocess.CalledProcessError as e:
            failures.append(
                f"Target '{target}' failed with exit code {e.returncode}:\n"
                f"stdout: {e.stdout}\n"
                f"stderr: {e.stderr}"
            )
        
        except subprocess.TimeoutExpired:
            failures.append(f"Target '{target}' timed out (>5s)")
    
    if failures:
        msg = ["Make target dry-run failures:", ""]
        msg.extend(failures)
        raise AssertionError("\n\n".join(msg))
    
    total_targets = len(targets) + len(targets_with_args)
    print(f"\n✓ Make targets verified: {total_targets} targets OK")
