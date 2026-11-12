"""FastAPI web app for Cell Edge Analysis: serves the front end in static/ and the JSON API under /api.

Run with `python run_web.py` (http://127.0.0.1:8124, local only). `scripts/build_static.py` exports every path in
STATIC_ENDPOINTS to JSON for the GitHub Pages site, so keep that list in step with the GET routes below.

The analysis page runs the JavaScript port (static/edge_engine.js) in the browser in both modes. The local app adds:
POST /api/tiff reads any TIFF with tifffile (compressed files too), and POST /api/analyse re-runs the same frames with
the repo's own Python step functions (web/analysis.py) so the browser result can be checked against Python.
"""
import base64
import json
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from web import analysis  # noqa: I001  (puts the repo root on sys.path first)
from web.tiff_io import read_stack

STATIC = Path(__file__).resolve().parent / "static"
MAX_UPLOAD_BYTES = 200 * 1024 * 1024

app = FastAPI(title="Cell Edge Analysis")
app.mount("/static", StaticFiles(directory=STATIC), name="static")

# The nine pipeline steps, as the README and run_all_steps.py describe them; "web" marks those the browser runs.
STEPS = [
    {"n": 1, "script": "step1_data_loading.py", "name": "Data loading", "web": True,
     "text": "Loads the PIEZO1 image stack and the cell mask stack; optional background subtraction (a histogram "
             "percentile per frame) and per-frame normalisation to the brightest pixel, times a scale factor."},
    {"n": 2, "script": "step2_edge_detection.py", "name": "Edge detection", "web": True,
     "text": "Finds the cell edge as the longest 0.5-level contour of each binary mask (skimage find_contours), "
             "optionally smoothed with a Gaussian along the contour (endpoints kept for open edges)."},
    {"n": 3, "script": "step3_displacement_calculation.py", "name": "Displacement", "web": False,
     "text": "Vertical displacement of the uppermost edge point at every integer x between consecutive frames."},
    {"n": 4, "script": "step4_movement_classification.py", "name": "Movement classification", "web": False,
     "text": "Classifies each frame pair as extruding, retracting or stable from its mean displacement."},
    {"n": 5, "script": "step5_edge_sampling.py", "name": "Edge sampling", "web": True,
     "text": "Picks sampling points along the edge (per_frame, fixed_x, dense or displacement_like), keeping the "
             "uppermost or lowermost edge point at each x."},
    {"n": 6, "script": "step6_sampling_rectangles.py", "name": "Sampling rectangles", "web": True,
     "text": "Places a width x depth rectangle at each point (vertical, or along the inward edge normal with optional "
             "flip / angle search) and accepts it if enough of it lies inside the cell mask."},
    {"n": 7, "script": "step7_intensity_extraction.py", "name": "Intensity extraction", "web": True,
     "text": "Mean PIEZO1 intensity of the pixels inside each accepted rectangle: the fluorescence profile along "
             "the edge."},
    {"n": 8, "script": "step8_movement_assignment.py", "name": "Movement assignment", "web": False,
     "text": "Pairs each intensity measurement with the local edge displacement (past or future frame pair)."},
    {"n": 9, "script": "step9_correlation_analysis.py", "name": "Correlation", "web": False,
     "text": "Pearson correlation and binned statistics of intensity versus local edge movement."},
]


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/info")
def info():
    """Project summary, the pipeline steps and the pipeline's default parameters (run_all_steps.PIPELINE_CONFIG)."""
    return {
        "title": "Cell Edge Analysis",
        "repo": "cell_edge_analysis",
        "description": "Fluorescence along a moving cell edge: PIEZO1 intensity sampled in rectangles just inside "
                       "the edge of a masked cell, frame by frame, and its relation to edge movement.",
        "steps": STEPS,
        "defaults": analysis.default_params(),
        "choices": {"sampling_method": analysis.SAMPLING_METHODS, "y_selection": analysis.Y_SELECTIONS,
                    "rotation_method": analysis.ROTATION_METHODS},
        "demo": {"image": "static/demo/demo_piezo1.tif", "mask": "static/demo/demo_Mask.tif",
                 "note": "SYNTHETIC stack written by scripts/make_demo_data.py (6 frames, 128 x 192 px, fixed seed): "
                         "a wavy moving edge with a fluorescent band just inside it. Not measured data."},
        "file_patterns": {"image": run_all_steps_patterns("IMAGE_PATTERNS"),
                          "mask": run_all_steps_patterns("MASK_PATTERNS")},
    }


def run_all_steps_patterns(key):
    return list(analysis.run_all_steps.PIPELINE_CONFIG[key])


async def _read(upload: UploadFile) -> bytes:
    data = await upload.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File too large for the web app (200 MB); use run_all_steps.py for big stacks.")
    return data


@app.post("/api/tiff")
async def tiff(file: UploadFile = File(...)):
    """Read a TIFF stack with tifffile; float32 pixels as base64 plus shape and the file's own pixel size."""
    try:
        stack, um, source = read_stack(await _read(file))
    except HTTPException:
        raise
    except Exception as e:  # tifffile raises many types for unreadable files
        raise HTTPException(400, f"Could not read {file.filename}: {e}")
    return {"name": file.filename, "shape": list(stack.shape), "um_per_px": um, "scale_source": source,
            "data": base64.b64encode(stack.tobytes()).decode("ascii")}


@app.post("/api/analyse")
async def analyse(image: UploadFile = File(...), mask: UploadFile = File(...), params: str = Form("{}"),
                  frames: str = Form("")):
    """Run the repo's Python steps 1, 2, 5, 6, 7 on the uploaded stacks (frames: comma-separated indices)."""
    try:
        img, _, _ = read_stack(await _read(image))
        msk, _, _ = read_stack(await _read(mask))
        sel = [int(f) for f in frames.split(",") if f.strip()] or None
        if sel and any(f < 0 or f >= img.shape[0] for f in sel):
            raise ValueError(f"frame index out of range (0..{img.shape[0] - 1})")
        return analysis.to_json(analysis.run(img, msk, json.loads(params or "{}"), sel))
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(400, str(e))


# GET paths (without the /api prefix) written to the static site as api/<path>.json.
STATIC_ENDPOINTS = ["/info"]
