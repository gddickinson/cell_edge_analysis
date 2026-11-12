"""Web interface tests: every exported endpoint answers, the static build is complete, and the JS engine tests pass.

Run: python -m pytest -q tests/test_web.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web.app import STATIC, STATIC_ENDPOINTS, app  # noqa: E402

client = TestClient(app)


def test_index_served():
    r = client.get("/")
    assert r.status_code == 200 and "static/main.js" in r.text


@pytest.mark.parametrize("path", STATIC_ENDPOINTS)
def test_endpoint(path):
    r = client.get("/api" + path)
    assert r.status_code == 200, r.text
    assert r.json() is not None


def test_static_build(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_static
    build_static.build(tmp_path / "site")
    assert (tmp_path / "site" / "index.html").read_text().count("APP_STATIC") == 1
    for path in STATIC_ENDPOINTS:
        assert (tmp_path / "site" / "api" / (path.strip("/") + ".json")).exists()


def test_static_assets_referenced_exist():
    html = (STATIC / "index.html").read_text()
    for name in ("style.css", "main.js"):
        assert f"static/{name}" in html and (STATIC / name).exists()


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_js_engine():
    tests = sorted(STATIC.glob("*.test.mjs"))
    for t in tests:
        r = subprocess.run(["node", str(t)], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr


# ---- project-specific API tests ---------------------------------------------------------------------------------
DEMO = STATIC / "demo"


def test_info_defaults_come_from_pipeline_defaults():
    from pipeline_defaults import DEFAULTS
    d = client.get("/api/info").json()
    assert d["defaults"]["smoothing_sigma"] == DEFAULTS["step2"]["smoothing_sigma"]
    assert d["defaults"]["rotation_method"] == DEFAULTS["step6"]["rotation_method"]
    assert [s["n"] for s in d["steps"]] == list(range(1, 10))
    assert (STATIC / d["demo"]["image"].removeprefix("static/")).exists()


def test_tiff_endpoint_reads_demo_with_pixel_size():
    r = client.post("/api/tiff", files={"file": ("demo_piezo1.tif", (DEMO / "demo_piezo1.tif").read_bytes())})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["shape"] == [6, 128, 192] and abs(d["um_per_px"] - 0.16) < 1e-6


def test_tiff_endpoint_rejects_garbage():
    r = client.post("/api/tiff", files={"file": ("x.tif", b"not a tiff")})
    assert r.status_code == 400


def test_analyse_endpoint_runs_python_steps():
    files = {"image": ("i.tif", (DEMO / "demo_piezo1.tif").read_bytes()),
             "mask": ("m.tif", (DEMO / "demo_Mask.tif").read_bytes())}
    r = client.post("/api/analyse", files=files, data={"params": '{"target_points_displacement": 5}', "frames": "2"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["n_frames"] == 6 and [f["frame"] for f in d["frames"]] == [2]
    rects = d["frames"][0]["rects"]
    assert rects and all(r["intensity"] is not None for r in rects if r["accepted"])


def test_analyse_endpoint_rejects_bad_params():
    files = {"image": ("i.tif", (DEMO / "demo_piezo1.tif").read_bytes()),
             "mask": ("m.tif", (DEMO / "demo_Mask.tif").read_bytes())}
    r = client.post("/api/analyse", files=files, data={"params": '{"rotation_method": "spin"}'})
    assert r.status_code == 400
