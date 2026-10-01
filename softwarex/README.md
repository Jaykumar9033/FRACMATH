# SoftwareX revision package

This folder contains the SoftwareX manuscript draft, figure sources, plotting
scripts, and the preserved verification data for the corrected 2D FRACMATH
implementation. The 2D MATLAB and UMAT source files are also copied here
under `reproducibility/` so the package can be run independently; the
repository's primary code entry points are under `../3pb/`.

The manuscript is a draft. Its software metadata still needs a permanent
tagged-release link and DOI before submission. The historical `v1.0.0`
release/DOI describe the earlier implementation and must not be used to
identify this revision.

## Contents

| Path | Contents |
| --- | --- |
| `manuscript.tex`, `manuscript.pdf`, `figures/` | SoftwareX paper and figures |
| `plot_verified_figures.py` | Regenerates corrected 2D figures from preserved `.mat` and CSV data |
| `rebuild_3d_figures.py`, `figure_sources/` | Recomposes archived 3D image panels with larger labels and a shared color bar |
| `compare_solver_diagnostics.py`, `reproducibility/solver_diagnostics.json` | Parses preserved MATLAB and Abaqus timing records without assigning unmeasured UMAT time |
| `reproducibility/2d/` | Corrected MATLAB solver, mesh, and material-point energy check |
| `reproducibility/results_1000/`, `results_10000/` | Preserved MATLAB step-size study |
| `reproducibility/abaqus/` | Corrected UMAT, job builder, extracted fields, and diagnostics |
| `REPRODUCE.md` | Exact run commands and limitations |

The 3D panels are retained as qualitative examples from the earlier
submission. Their numerical cases were not rerun for this revision. The
corrected 2D results are based on one mesh and do not prove structural mesh
objectivity or a runtime advantage over Abaqus.
