# Contributing

Thanks for contributing to `smooth-radar-skill`.

## Scope
This repository intentionally maintains one visual style:
- `dual_anchor_custom` per-axis display mapping with fixed, de-periodized anchors
- closed centripetal Catmull–Rom interpolation (`alpha=0.5`)

Please do not add alternative radar styles or automatic/random anchor generation without discussing the scientific and visual implications first.

## Before submitting a change
1. Preserve raw values unchanged.
2. Preserve within-axis model ordering.
3. Add or update tests for mapping, extrema, and curve geometry.
4. Render the anonymized example and inspect PNG, SVG, and PDF.
5. Ensure the caption/audit clearly states that cross-axis radii are not directly comparable.

## Data and privacy
Do not commit unpublished patient-level data, identifiable cohort information, private model names, API keys, credentials, or private paths. Use anonymized examples only.
