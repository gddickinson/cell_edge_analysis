"""Write tests/fixtures/edge_fixture.json: Python reference values for the JS port (web/static/edge_engine.js).

Everything is computed by the repo's own code (via web/analysis.py) or by the library calls it makes
(skimage.measure.find_contours, scipy.ndimage.gaussian_filter1d, numpy.percentile):
  - contours: find_contours(mask, 0.5) on small masks with saddles, holes, several blobs and border contact
  - gaussian: gaussian_filter1d in 'wrap' and 'reflect' modes, including sigma larger than the signal
  - percentile: numpy.percentile of a float32 demo frame
  - pipeline: steps 1, 2, 5, 6, 7 on the demo stack (web/static/demo) and on a small closed-blob stack, for several
    parameter sets covering every sampling and rotation method
tests/test_edge_fixture.py checks the fixture is current; web/static/edge_engine.test.mjs checks JS against it.

Run: python scripts/make_edge_fixture.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import tifffile
from scipy.ndimage import gaussian_filter1d
from skimage import measure

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from web import analysis  # noqa: E402

OUT = ROOT / "tests" / "fixtures" / "edge_fixture.json"
DEMO = ROOT / "web" / "static" / "demo"

CASES = [
    {"name": "defaults", "params": {}, "frames": None, "full_edges": True},
    {"name": "per_frame_none", "params": {"sampling_method": "per_frame", "n_points": 12, "rotation_method": "none"}},
    {"name": "fixed_x_gaps_flip", "params": {"sampling_method": "fixed_x", "n_points": 100, "rotation_method": "flip",
                                             "min_cell_coverage": 0.9}},
    {"name": "dense_search", "params": {"sampling_method": "dense", "rotation_method": "search", "width": 9,
                                        "depth": 15, "min_cell_coverage": 0.97}, "frames": [3]},
    {"name": "raw_lowermost_search", "params": {"smooth_edges": False, "subtract_background": False,
                                                "normalize_frames": False, "exclude_endpoints": False,
                                                "target_points_displacement": 7, "y_selection": "lowermost",
                                                "rotation_method": "search", "rotation_search_angles": 12,
                                                "min_cell_coverage": 0.5}},
    {"name": "sigma3_flip", "params": {"smoothing_sigma": 3.5, "background_percentile": 25,
                                       "normalization_scale": 1.0, "rotation_method": "flip",
                                       "min_cell_coverage": 0.95, "width": 11, "depth": 31}},
]
BLOB_CASES = [
    {"name": "blob_none", "params": {"sampling_method": "per_frame", "n_points": 9, "rotation_method": "none",
                                     "width": 5, "depth": 8, "smoothing_sigma": 4.0}, "full_edges": True},
    {"name": "blob_search", "params": {"sampling_method": "dense", "rotation_method": "search", "width": 5,
                                       "depth": 12, "min_cell_coverage": 0.99, "smoothing_sigma": 40.0,
                                       "y_selection": "lowermost"}, "full_edges": True},
]


def contour_masks():
    rng = np.random.default_rng(3)
    masks = []
    m = np.zeros((7, 8), np.uint8); m[2:5, 2:6] = 1; m[3, 3] = 0; masks.append(m)              # blob with a hole
    m = np.array([[1, 0, 0, 1], [0, 1, 1, 0], [0, 1, 1, 0], [1, 0, 0, 1]], np.uint8); masks.append(m)  # saddles
    m = np.zeros((9, 9), np.uint8); m[0:4, 0:3] = 1; m[5:, 4:] = 1; m[1, 7] = 1; masks.append(m)  # border + blobs
    masks.append((rng.random((14, 17)) > 0.55).astype(np.uint8))                                 # random speckle
    masks.append((rng.random((20, 20)) > 0.4).astype(np.uint8))
    return masks


def blob_stack():
    rng = np.random.default_rng(11)
    rr, cc = np.mgrid[0:48, 0:56].astype(float)
    masks, images = [], []
    for t in range(2):
        r = 15 + 3 * np.sin(4 * np.arctan2(rr - 24, cc - 28) + t)
        masks.append(((rr - 24) ** 2 + (cc - 28 - 2 * t) ** 2 < r ** 2).astype(np.uint8))
        images.append(np.round(rng.normal(200, 30, (48, 56))).clip(0).astype(np.uint16))
    return np.array(images), np.array(masks)


def run_case(images, masks, case):
    res = analysis.to_json(analysis.run(images, masks, case["params"], case.get("frames")))
    for f in res["frames"]:
        if not case.get("full_edges"):
            e = np.array(f["edge"], float).reshape(-1, 2)
            f["edge"] = {"n": len(e), "sum": e.sum(axis=0).tolist() if len(e) else [0, 0],
                         "first": e[0].tolist() if len(e) else None, "last": e[-1].tolist() if len(e) else None}
    return {"name": case["name"], "params": res["params"], "frames_requested": case.get("frames"), "result": res}


def build():
    images = tifffile.imread(DEMO / "demo_piezo1.tif")
    masks = tifffile.imread(DEMO / "demo_Mask.tif")
    bimg, bmask = blob_stack()
    sig = np.sin(np.arange(23) / 3.0) * 10 + np.arange(23)
    frame0 = images[0].astype(np.float32)
    return {
        "contours": [{"mask": m.tolist(), "contours": [c.tolist() for c in measure.find_contours(m, 0.5)]}
                     for m in contour_masks()],
        "gaussian": [{"x": sig.tolist(), "sigma": s, "mode": mode,
                      "y": gaussian_filter1d(sig, s, mode=mode).tolist()}
                     for s in (0.7, 2.0, 20.0) for mode in ("wrap", "reflect")],
        "percentile": [{"p": p, "value": float(np.percentile(frame0, p))} for p in (0, 10, 25, 37.5, 100)],
        "demo": {"image": "web/static/demo/demo_piezo1.tif", "mask": "web/static/demo/demo_Mask.tif",
                 "shape": list(images.shape), "checksum": [int(images.sum()), int((masks > 0).sum())]},
        "pipeline": [run_case(images, masks, c) for c in CASES],
        "blob": {"images": bimg.tolist(), "masks": bmask.tolist(),
                 "pipeline": [run_case(bimg, bmask, c) for c in BLOB_CASES]},
    }


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(build(), separators=(",", ":")))
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
