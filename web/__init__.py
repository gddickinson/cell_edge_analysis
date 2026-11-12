"""Web interface for the cell edge analysis pipeline (FastAPI + plain ES-module front end).

- app.py       FastAPI app: front end, JSON API under /api, STATIC_ENDPOINTS for the static GitHub Pages export
- analysis.py  runs the repo's step 1/2/5/6/7 functions on in-memory stacks (API + JS-vs-Python fixture)
- tiff_io.py   reads uploaded TIFF stacks with tifffile (incl. compressed files) and their pixel size
- static/      front end; edge_engine.js + contours.js are the JS port tested against Python (*.test.mjs)
"""
