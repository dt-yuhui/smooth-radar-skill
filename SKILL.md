---
name: smooth-radar-skill
description: Create smooth-radar scientific radar charts with fixed de-periodized per-axis dual anchors, closed centripetal Catmull–Rom curves, raw extrema labels and publication-ready exports.
---

# Smooth Radar Skill

One supported style only: `dual_anchor_custom` radial mapping + `centripetal_catmull_rom` closed smooth curve.

## Scale mapping
For each axis j, map its raw minimum and maximum across models to fixed `inner_anchor[j]` and `outer_anchor[j]`:

`r_ij = a_j + (x_ij - min_j) / (max_j - min_j) * (b_j - a_j)`

All models on an axis share the same affine mapping. Anchors are fixed, manually specified and de-periodized. Do not generate them randomly, with sine waves, or from odd/even parity. Raw values are never modified. Within-axis ordering is preserved; cross-axis radial distances are not comparable. Never rank models by radar area.

## Curve
Use closed centripetal Catmull–Rom interpolation: `catmull_rom_closed(xy, samples=40, alpha=0.5)`. Here periodic/closed means the last axis connects back to the first; it does not mean the anchor pattern is periodic. Preserve original mapped data markers. Curves between categorical axes are visual interpolation only.

## Annotations and layout
- Determine min/max from full-precision raw values before rounding.
- Default label precision: 3 decimals.
- Preserve the configured tie tolerance; tied extrema use a neutral color.
- Text labels may move to avoid collisions; data points must not move.
- Small local curve gaps may be used around extrema labels; never shift or delete data points.
- White background, Arial/sans-serif, light rings and dashed spokes, subtle task-group label frames.
- Draw baseline models first and highlight model last.
- Use configured line widths in points.

## Anonymized example
`assets/example_config.json` and `assets/example_presets.json` contain the supplied five-model, twelve-axis example. Model names are anonymized as Model A–E. Numeric values, axes, colors, anchors, curve settings and annotation settings are retained.

## Run
`python scripts/plot_smooth_radar.py --preset example --outdir output/example`

Custom data: copy `assets/example_config.json`, replace the models/axes/values/colors and set one fixed inner and outer anchor per axis, then run `python scripts/plot_smooth_radar.py --config my_config.json --outdir output/my_radar`.

Outputs: PNG, SVG, PDF and `scale_audit.json`.

## Caption disclosure
"Axis-specific display ranges were used to visualize task-wise profiles. Within-axis model ordering is preserved; radial distances across axes are not directly comparable. Curves between categorical axes are visual interpolation only."
