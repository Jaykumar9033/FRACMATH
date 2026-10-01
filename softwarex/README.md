# SoftwareX package

This folder contains the SoftwareX manuscript draft, figure sources, plotting
scripts, and the preserved verification data for the 2D FRACMATH
implementation. The 2D MATLAB and UMAT source files are also copied here
under `reproducibility/` so the package can be run independently; the
repository's primary code entry points are under `../3pb/`.

The manuscript metadata identifies the source and study data by an immutable GitHub commit.

## Contents

| Path | Contents |
| --- | --- |
| `manuscript.tex`, `manuscript.pdf`, `figures/` | SoftwareX paper and figures |
| `plot_verified_figures.py` | Regenerates 2D figures from preserved `.mat` and CSV data |
| `rebuild_3d_figures.py`, `figure_sources/` | Recomposes archived 3D image panels with larger labels and a shared color bar |
| `compare_solver_diagnostics.py`, `reproducibility/solver_diagnostics.json` | Parses preserved MATLAB and Abaqus timing records without assigning unmeasured UMAT time |
| `reproducibility/2d/` | MATLAB solver, mesh, and material-point energy check |
| `reproducibility/results_1000/`, `results_10000/` | Preserved MATLAB step-size study |
| `reproducibility/abaqus/` | UMAT, job builder, extracted fields, and diagnostics |
| `run_mesh_study.py`, `analyze_mesh_study.py`, `MESH_STUDY.md` | Controlled mesh family, regularization control, energy/increment checks, and Abaqus scaling protocol |
| `reproducibility/mesh_study/` | Exact meshes, completed-job diagnostics, response/energy histories, summaries, and source hashes |
| `REPRODUCE.md` | Exact run commands and limitations |

The 3D panels illustrate damage workflows qualitatively. Quantitative 3D validation is outside the study scope. The 2D study compares three controlled meshes. This evidence is limited to one geometry and mesh family; it does not establish general mesh independence or a runtime advantage over Abaqus.
