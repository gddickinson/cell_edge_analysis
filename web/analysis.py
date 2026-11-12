"""Run the repo's own step 1, 2, 5, 6 and 7 code on in-memory image + mask stacks (for the web API and the fixture).

Nothing here re-implements the analysis: it calls the step modules' functions (step1_data_loading.subtract_background,
step2_edge_detection.detect_cell_edge / smooth_edge, step5_edge_sampling.sample_all_edges,
step6_sampling_rectangles.create_rectangles_for_frame, step7_intensity_extraction.extract_intensity_from_rectangle).
Those functions read their module's CONFIG dict, so each run sets the CONFIG keys under a lock and restores them after.

Units: everything is in pixels, as in the pipeline. Coordinates are (row, col) = (y, x) with the pixel-centre
convention of skimage.measure.find_contours (pixel (r, c) has its centre at (r, c)).
"""
import contextlib
import io
import os
import sys
import threading
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLBACKEND", "Agg")  # the step modules import pyplot at import time

import pipeline_defaults  # noqa: E402  (the single source of pipeline defaults)
import step1_data_loading as s1  # noqa: E402
import step2_edge_detection as s2  # noqa: E402
import step5_edge_sampling as s5  # noqa: E402
import step6_sampling_rectangles as s6  # noqa: E402
import step7_intensity_extraction as s7  # noqa: E402

_LOCK = threading.Lock()

# Choices exactly as offered by the step scripts' argparse options.
SAMPLING_METHODS = ["per_frame", "fixed_x", "dense", "displacement_like"]
Y_SELECTIONS = ["uppermost", "lowermost"]
ROTATION_METHODS = ["none", "flip", "search", "vertical"]
# Types as parsed by the step scripts' argparse options (type=int / type=float / true|false / choice strings).
INT_KEYS = {"n_points", "target_points_displacement", "depth", "width", "rotation_search_angles"}
BOOL_KEYS = {"normalize_frames", "subtract_background", "smooth_edges", "exclude_endpoints"}
STR_KEYS = {"sampling_method", "y_selection", "rotation_method"}


def default_params():
    """The web parameters, with defaults from pipeline_defaults.DEFAULTS (shared with the scripts and the GUI)."""
    c = pipeline_defaults.DEFAULTS
    p1, p2, p5, p6 = c["step1"], c["step2"], c["step5"], c["step6"]
    return {
        "normalize_frames": p1["normalize_frames"], "normalization_scale": p1["normalization_scale"],
        "subtract_background": p1["subtract_background"], "background_percentile": p1["background_percentile"],
        "smooth_edges": p2["smooth_edges"], "smoothing_sigma": p2["smoothing_sigma"],
        "sampling_method": p5["sampling_method"], "n_points": p5["n_points"],
        "exclude_endpoints": p5["exclude_endpoints"], "target_points_displacement": p5["target_points_displacement"],
        "y_selection": p5["y_selection"],
        "depth": p6["depth"], "width": p6["width"], "min_cell_coverage": p6["min_cell_coverage"],
        "rotation_method": p6["rotation_method"], "rotation_search_angles": p6["rotation_search_angles"],
    }


def clean_params(params):
    """Defaults overlaid with the given values, type-checked against the step scripts' options."""
    p = default_params()
    for k, v in (params or {}).items():
        if k not in p:
            raise ValueError(f"unknown parameter {k!r}")
        if k in BOOL_KEYS:
            p[k] = v if isinstance(v, bool) else str(v).lower() == "true"
        elif k in INT_KEYS:
            p[k] = int(v)
        elif k in STR_KEYS:
            p[k] = str(v)
        else:
            p[k] = float(v)
    if p["sampling_method"] not in SAMPLING_METHODS:
        raise ValueError(f"sampling_method must be one of {SAMPLING_METHODS}")
    if p["y_selection"] not in Y_SELECTIONS:
        raise ValueError(f"y_selection must be one of {Y_SELECTIONS}")
    if p["rotation_method"] not in ROTATION_METHODS:
        raise ValueError(f"rotation_method must be one of {ROTATION_METHODS}")
    if p["smooth_edges"] and p["smoothing_sigma"] <= 0:
        raise ValueError("smoothing_sigma must be > 0")
    if p["n_points"] < 1 or p["target_points_displacement"] < 1 or p["rotation_search_angles"] < 1:
        raise ValueError("point counts and search angles must be >= 1")
    if p["width"] <= 0 or p["depth"] <= 0:
        raise ValueError("rectangle width and depth must be > 0")
    return p


@contextlib.contextmanager
def _config(module, values):
    old = {k: module.CONFIG.get(k, None) for k in values}
    missing = [k for k in values if k not in module.CONFIG]
    module.CONFIG.update(values)
    try:
        yield
    finally:
        module.CONFIG.update(old)
        for k in missing:
            module.CONFIG.pop(k, None)


def as_stacks(images, masks):
    """(T, H, W) image and binary-mask stacks as step 1 loads them (2-D inputs become one frame)."""
    images, masks = np.asarray(images), (np.asarray(masks) > 0).astype(np.uint8)
    if images.ndim == 2:
        images = images[np.newaxis]
    if masks.ndim == 2:
        masks = masks[np.newaxis]
    if images.ndim != 3 or masks.ndim != 3:
        raise ValueError(f"expected 2-D or 3-D stacks, got image {images.shape} and mask {masks.shape}")
    if images.shape[1:] != masks.shape[1:]:
        raise ValueError(f"image frames are {images.shape[1:]} but mask frames are {masks.shape[1:]}")
    if images.shape[0] != masks.shape[0]:
        raise ValueError(f"image stack has {images.shape[0]} frames but mask stack has {masks.shape[0]}")
    return images, masks


def run(images, masks, params=None, frames=None):
    """Steps 1, 2, 5, 6, 7 on the stacks. `frames` limits steps 6-7 to those frame indices (edges and sampling
    always use every frame, because 'fixed_x' sampling needs the x-range common to all frames)."""
    p = clean_params(params)
    images, masks = as_stacks(images, masks)
    frames = list(range(images.shape[0])) if frames is None else [int(f) for f in frames]
    with _LOCK, contextlib.redirect_stdout(io.StringIO()):
        with _config(s1, {"BACKGROUND_PERCENTILE": p["background_percentile"],
                          "NORMALIZATION_SCALE": p["normalization_scale"]}):
            if p["subtract_background"]:
                images = s1.subtract_background(images)
            if p["normalize_frames"]:
                images = s1.normalize_frames(images)
        edges = []
        for m in masks:
            e = s2.detect_cell_edge(m)
            if p["smooth_edges"] and len(e) > 0:
                e = s2.smooth_edge(e, p["smoothing_sigma"])
            edges.append(e)
        with _config(s5, {"sampling_method": p["sampling_method"], "n_points": p["n_points"],
                          "exclude_endpoints": p["exclude_endpoints"], "y_selection": p["y_selection"],
                          "target_points_displacement": p["target_points_displacement"]}):
            sampled = s5.sample_all_edges(edges)
        out = []
        with _config(s6, {"depth": p["depth"], "width": p["width"], "min_cell_coverage": p["min_cell_coverage"],
                          "rotation_method": p["rotation_method"],
                          "rotation_search_angles": p["rotation_search_angles"]}):
            for i in frames:
                rects = []
                if len(sampled[i]) > 0 and len(edges[i]) > 0:
                    rects = s6.create_rectangles_for_frame(sampled[i], edges[i], masks[i])
                for r in rects:
                    r["intensity"] = (s7.extract_intensity_from_rectangle(images[i], r["pixels"])
                                      if r["accepted"] else np.nan)
                out.append({"frame": i, "edge": edges[i], "sampled": sampled[i], "rects": rects})
    return {"params": p, "n_frames": int(images.shape[0]), "shape": list(images.shape[1:]), "frames": out}


def _num(v):
    v = float(v)
    return None if np.isnan(v) else v


def to_json(result):
    """JSON-safe form of run()'s result (NaN -> null; pixel lists replaced by their count)."""
    frames = []
    for f in result["frames"]:
        frames.append({
            "frame": f["frame"],
            "edge": [[_num(a), _num(b)] for a, b in np.asarray(f["edge"]).reshape(-1, 2)],
            "sampled": [[_num(a), _num(b)] for a, b in np.asarray(f["sampled"]).reshape(-1, 2)],
            "rects": [{"point_index": int(r["point_index"]), "edge_point": [_num(v) for v in r["edge_point"]],
                       "corners": [[_num(a), _num(b)] for a, b in np.asarray(r["corners"])],
                       "coverage": _num(r["coverage"]), "accepted": bool(r["accepted"]),
                       "rotation_tried": bool(r["rotation_tried"]), "rotation_angle": float(r["rotation_angle"]),
                       "n_pixels": int(len(r["pixels"])), "intensity": _num(r["intensity"])}
                      for r in f["rects"]],
        })
    return {"params": result["params"], "n_frames": result["n_frames"], "shape": result["shape"], "frames": frames}
