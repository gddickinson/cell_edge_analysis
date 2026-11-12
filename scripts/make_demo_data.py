"""Write the SYNTHETIC demo stack used by the web pages: web/static/demo/demo_piezo1.tif + demo_Mask.tif.

Not measured data. A scratch-assay-like geometry (the cell sheet fills the image below a wavy leading edge that moves
from frame to frame) with a fluorescent band just inside the edge whose brightness varies along x, plus Gaussian noise.
The files follow the pipeline's naming rule (`*piezo1.tif`, `*Mask.tif`) and are uncompressed so the browser can read
them. Deterministic (fixed seed).

Run: python scripts/make_demo_data.py
"""
from pathlib import Path

import numpy as np
import tifffile

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "static" / "demo"
DEMO = {"frames": 6, "height": 128, "width": 192, "seed": 7, "um_per_px": 0.16}


def edge_row(x, t):
    """Row of the leading edge at column x in frame t (the cell lies below it)."""
    return 48 + 10 * np.sin(2 * np.pi * x / 96 + 0.5 * t) + 4 * np.sin(2 * np.pi * x / 37 - 0.8 * t)


def make_stack():
    T, H, W = DEMO["frames"], DEMO["height"], DEMO["width"]
    rng = np.random.default_rng(DEMO["seed"])
    rows, cols = np.mgrid[0:H, 0:W].astype(float)
    images = np.zeros((T, H, W), np.uint16)
    masks = np.zeros((T, H, W), np.uint8)
    for t in range(T):
        depth = rows - edge_row(cols, t)          # > 0 inside the cell
        inside = depth > 0
        band = 250 * (0.5 + 0.5 * np.sin(2 * np.pi * cols / 64 + 0.3 * t)) * np.exp(-np.clip(depth, 0, None) / 6)
        img = 100 + inside * (80 + band) + rng.normal(0, 8, (H, W))
        images[t] = np.clip(np.round(img), 0, 65535).astype(np.uint16)
        masks[t] = inside.astype(np.uint8) * 255
    return images, masks


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    images, masks = make_stack()
    res = (1 / DEMO["um_per_px"], 1 / DEMO["um_per_px"])
    meta = {"unit": "um", "axes": "TYX"}
    tifffile.imwrite(OUT / "demo_piezo1.tif", images, imagej=True, resolution=res, metadata=meta)
    tifffile.imwrite(OUT / "demo_Mask.tif", masks, imagej=True, resolution=res, metadata=meta)
    print(f"wrote {OUT}/demo_piezo1.tif and demo_Mask.tif: {images.shape}")


if __name__ == "__main__":
    main()
