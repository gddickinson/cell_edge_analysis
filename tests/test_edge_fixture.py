"""The JS-vs-Python fixture (tests/fixtures/edge_fixture.json) is still what the repo's Python code produces.

Regenerate with `python scripts/make_edge_fixture.py` after changing steps 1, 2, 5, 6, 7 or the demo data.
Numbers are compared with a tolerance (libm differs in the last digit between platforms).
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import make_edge_fixture  # noqa: E402


def _same(a, b, path="", out=None):
    if isinstance(a, dict):
        assert isinstance(b, dict) and a.keys() == b.keys(), path
        for k in a:
            _same(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        assert isinstance(b, list) and len(a) == len(b), f"{path}: length {len(a)} vs {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            _same(x, y, f"{path}[{i}]")
    elif isinstance(a, float) or isinstance(b, float):
        assert a is not None and b is not None, path
        assert math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9), f"{path}: {a} vs {b}"
    else:
        assert a == b, f"{path}: {a!r} vs {b!r}"


def test_fixture_is_current():
    stored = json.loads(make_edge_fixture.OUT.read_text())
    fresh = json.loads(json.dumps(make_edge_fixture.build()))
    _same(fresh, stored)
