# SoftwareX package

This folder contains the SoftwareX manuscript draft, figure sources, plotting
scripts, and the preserved verification data for the 2D and 3D FRACMATH
implementation. The 2D MATLAB and UMAT source files are also copied here
under `reproducibility/` so the package can be run independently; the
repository's primary code entry points are under `../3pb/`.

The manuscript metadata identifies the source and study data by an immutable GitHub commit.

## Contents

For a first MATLAB run, open [`start_here.m`](start_here.m) and press Run.
The [beginner guide](BEGINNER_GUIDE.md) explains settings, units, array
dimensions, the load-step algorithm, and how to compare numerical outputs.

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
| `reproducibility/timing_repeats/` | Three observations of each of 30 configurations: medians, ranges, raw records and exact response-repeat checks |
| `reproducibility/nooru_25mm_coarse/` | Published 25 mm notch geometry, completed coarse TET4 run, digitized experimental comparison and local material/history checks |
| `plot_nooru_proportional.py`, `reproducibility/nooru_proportional/` | Shear and normal response diagnostics with explicit equilibrium-failure markers |
| `REPRODUCE.md` | Exact run commands and limitations |

The 3D damage panels illustrate workflows qualitatively. The completed coarse pure-tension case with the published 25 mm notch geometry supplies a quantitative experimental comparison; one completed mesh does not establish 3D mesh convergence. The 2D study compares three controlled meshes. These studies do not establish general mesh independence or a runtime advantage over Abaqus.

The [published-geometry coarse 3D comparison](reproducibility/nooru_25mm_coarse/README.md) uses local gauge control and strict equilibrium. Its 35,917 TET4 elements and 21,828 DOFs reach the full gauge-displacement target in 608 accepted increments, with eight rejected trials and a maximum relative equilibrium residual of 8.917e-7. The peak load is 16.6415 kN versus the digitized experimental 19.8529 kN (16.18% below); normalized curve RMS error is 9.27%. Thirty-two local tetrahedron size/direction tests, the compression mapping and eight rotating-direction history checks pass. The separate [illustrative geometry](reproducibility/experimental_3d/README.md) uses 20 mm notches and is not the published 25 mm specimen.


## Size, mesh, CPU and hybrid GPU evidence

See [SCALING_STUDY.md](SCALING_STUDY.md) for all 30 completed configurations, each measured three times (90 runs), response checks, median times, observed ranges, exact meshes and licensed-run/archive-replay commands. Saved MATLAB numerical arrays and Abaqus response CSVs match exactly between observations within each configuration. The [repeat archive](reproducibility/timing_repeats/README.md) preserves the full evidence. The hybrid GPU is functional and retains CPU sparse factorization; no GPU speedup is observed on this workstation. Abaqus SMP reaches a 2.90 speed ratio on the largest mesh. MATLAB load-loop and Abaqus analysis/output times have different scopes.

The medium/fine 3D mesh cases, separate Abaqus profiling and the beginner-entry 10,000-step reproduction check remain pending. The completed evidence is sufficient to describe the measured results and their limits; the remaining cases must pass their numerical checks before supporting further claims.
