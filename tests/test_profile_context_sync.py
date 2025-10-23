import subprocess
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_profile_context_up_to_date():
    """Verify the committed profile context matches the generated content from module contexts."""
    # --check exits 0 if OUT matches generated content, else nonzero
    subprocess.run(
        ["python3", "tools/build_profile_context.py", "--check"],
        cwd=ROOT,
        check=True
    )
