"""Regression: every entry point uses the same pipeline defaults (pipeline_defaults.DEFAULTS).

Before the fix the Tk GUI started with n_points 10 and target_points_displacement 5 (pipeline: 12 and 20), and step 8
run on its own (as the GUI runs it) used temporal_direction 'past' while run_all_steps.py passed 'future', so the GUI
and the batch pipeline gave different results on the same data.
"""
import importlib
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLBACKEND", "Agg")

STEPS = {"step1": "step1_data_loading", "step2": "step2_edge_detection", "step3": "step3_displacement_calculation",
         "step4": "step4_movement_classification", "step5": "step5_edge_sampling",
         "step6": "step6_sampling_rectangles", "step7": "step7_intensity_extraction",
         "step8": "step8_movement_assignment", "step9": "step9_correlation_analysis"}


def defaults():
    from pipeline_defaults import DEFAULTS
    return DEFAULTS


@pytest.mark.parametrize("step", list(STEPS))
def test_step_script_config_matches(step):
    cfg = {k.lower(): v for k, v in importlib.import_module(STEPS[step]).CONFIG.items()}
    for key, value in defaults()[step].items():
        assert cfg[key] == value, f"{STEPS[step]}.CONFIG[{key!r}] = {cfg[key]!r}, defaults say {value!r}"


def test_run_all_steps_uses_defaults():
    import run_all_steps
    for step in STEPS:
        assert run_all_steps.PIPELINE_CONFIG[step] == defaults()[step]


def test_web_uses_defaults():
    from web import analysis
    d, p = defaults(), analysis.default_params()
    assert p["n_points"] == d["step5"]["n_points"]
    assert p["target_points_displacement"] == d["step5"]["target_points_displacement"]
    assert p["smoothing_sigma"] == d["step2"]["smoothing_sigma"] and p["width"] == d["step6"]["width"]


def test_gui_initial_values_match():
    tk = pytest.importorskip("tkinter")
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("no display for Tk")
    root.withdraw()
    try:
        import cell_edge_analysis_gui as g
        gui = g.AnalysisGUI(root)
        d = defaults()
        pairs = {"normalize_frames": d["step1"], "normalization_scale": d["step1"], "subtract_background": d["step1"],
                 "background_percentile": d["step1"], "smooth_edges": d["step2"], "smoothing_sigma": d["step2"],
                 "min_movement_pixels": d["step3"], "arrow_scale": d["step3"], "movement_threshold": d["step4"],
                 "sampling_method": d["step5"], "n_points": d["step5"], "target_points_displacement": d["step5"]}
        for name, src in pairs.items():
            assert getattr(gui, name).get() == src[name], name
    finally:
        root.destroy()
