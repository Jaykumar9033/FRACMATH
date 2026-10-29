# Manuscript figure reproduction

Run from the repository root:

```powershell
python softwarex/verify_paper_figures.py --workspace C:/runs/figure_replay
```

The script executes each plot generator in a separate process and output
directory. It compares PNG pixels and PDF pixels rendered with Poppler.
All eight generated manuscript assets match. Two supplied geometry
illustrations match their archived source bytes. `summary.json` records
these checks; `asset_sha256.json` identifies the figure and image-source files.

This verifies reconstruction from preserved scientific data and supplied
illustrations. It does not convert qualitative damage panels or the failed
mixed-mode histories into equilibrium-verified simulations. The three-mesh
pure-tension study and 2D numerical examples have their own solver checks.
Image metadata, PDF dates, runtime and workstation-specific font behavior
are separate from numerical reproduction. The tested environment uses
Matplotlib, Pillow, NumPy, SciPy and Poppler on Windows.
