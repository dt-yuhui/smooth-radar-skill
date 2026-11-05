# Quick start

1. Copy this complete folder to `~/.agents/skills/smooth-radar-skill/` (macOS/Linux) or `%USERPROFILE%\.agents\skills\smooth-radar-skill\` (Windows).
2. Install: `python -m pip install -r requirements.txt`.
3. Reload Codex and invoke `$smooth-radar-skill`.

Render the anonymized example:
```bash
python scripts/plot_smooth_radar.py --preset example --outdir output/example
```

For your own data, copy `assets/example_config.json`, replace model names, axis labels, values and colors, and provide one inner/outer anchor per axis. Then run:
```bash
python scripts/plot_smooth_radar.py --config my_config.json --outdir output/my_radar
```

Outputs: PNG, SVG, PDF and `scale_audit.json`.
