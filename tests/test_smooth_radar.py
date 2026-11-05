import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from plot_smooth_radar import map_values, catmull_rom_closed

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/"assets"/"example_config.json").read_text())

def test_mapping_hits_each_axis_anchor():
    values = np.asarray(CFG["values"])
    radii, audit = map_values(values, CFG)
    for j in range(values.shape[1]):
        assert np.isclose(radii[:,j].min(), CFG["scale"]["inner_anchor"][j])
        assert np.isclose(radii[:,j].max(), CFG["scale"]["outer_anchor"][j])

def test_within_axis_order_is_preserved():
    values = np.asarray(CFG["values"])
    radii, _ = map_values(values, CFG)
    for j in range(values.shape[1]):
        order = np.argsort(values[:,j])
        assert np.all(np.diff(radii[order,j]) >= -1e-12)

def test_catmull_curve_closes_and_interpolates_vertices():
    theta = np.pi/2 - np.arange(8)*2*np.pi/8
    rad = np.array([.8,.9,.7,.6,.75,.95,.85,.7])
    pts = np.c_[rad*np.cos(theta), rad*np.sin(theta)]
    curve = catmull_rom_closed(pts, samples=20, alpha=.5)
    assert np.allclose(curve[0], curve[-1])
    assert np.allclose(curve[:-1:20], pts)

def test_example_is_anonymized():
    assert CFG["models"] == ["Model A", "Model B", "Model C", "Model D", "Model E"]
    assert CFG["style"]["highlight_model"] == "Model E"
