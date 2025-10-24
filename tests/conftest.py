import os, time, socket, subprocess, requests, pathlib, signal, sys
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _get_free_port():
    s = socket.socket()
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="session")
def server_base():
    """
    Start ./serve_dev.py on a free port serving the repo root.
    Yield the base URL for /interface-schemas and tear down after.
    """
    port = _get_free_port()
    env = os.environ.copy()
    cmd = [sys.executable, str(REPO_ROOT / "serve_dev.py"), "--root", str(REPO_ROOT), "--port", str(port)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=REPO_ROOT)

    base = f"http://localhost:{port}"
    # Wait until the context is reachable (up to 10s)
    probe = f"{base}/interface-schemas/dpc/contexts/v1.jsonld"
    ok = False
    for _ in range(100):
        try:
            r = requests.get(probe, timeout=0.2)
            if r.status_code == 200:
                ok = True
                break
        except Exception:
            pass
        time.sleep(0.1)
    if not ok:
        # dump some logs to help debugging
        try:
            if proc.stdout:
                out = proc.stdout.read().decode(errors="ignore")
                print("Server output:", out)
        except Exception:
            pass
        try:
            proc.terminate()
        except Exception:
            pass
        raise RuntimeError("Dev server did not start or /interface-schemas path not found")

    yield f"{base}/interface-schemas"

    # Teardown
    try:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
    except Exception:
        pass


# Dynamic test parametrization based on file discovery
CRATES_DIR = REPO_ROOT / "tests" / "crates"
VALID_DIR = CRATES_DIR / "valid"
INVALID_DIR = CRATES_DIR / "invalid"


def _json_files(dirpath: pathlib.Path):
    """Discover all .json and .jsonld files in a directory."""
    if not dirpath.exists():
        return []
    json_files = sorted(dirpath.glob("*.json"))
    jsonld_files = sorted(dirpath.glob("*.jsonld"))
    return sorted(json_files + jsonld_files)


def pytest_generate_tests(metafunc):
    """
    Parametrize tests that declare 'valid_crate_path' or 'invalid_crate_path'.
    
    Any test function with these parameters will be automatically parametrized
    over all discovered files in the corresponding directory.
    """
    if "valid_crate_path" in metafunc.fixturenames:
        paths = _json_files(VALID_DIR)
        if not paths:
            pytest.skip(f"No valid crates found under {VALID_DIR}")
        metafunc.parametrize(
            "valid_crate_path",
            [pytest.param(p, id=p.relative_to(VALID_DIR).as_posix()) for p in paths]
        )

    if "invalid_crate_path" in metafunc.fixturenames:
        paths = _json_files(INVALID_DIR)
        if not paths:
            # Gracefully handle empty invalid directory
            metafunc.parametrize("invalid_crate_path", [], ids=[])
        else:
            metafunc.parametrize(
                "invalid_crate_path",
                [pytest.param(p, id=p.relative_to(INVALID_DIR).as_posix()) for p in paths]
            )
