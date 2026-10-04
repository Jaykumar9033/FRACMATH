# SoftwareX package

This folder contains figure sources, plotting scripts, and the preserved
verification data for the 2D and 3D FRACMATH
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
| `figures/`, `tables/` | Reference figures and numerical tables reproduced by the scripts |
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
| `reproducibility/nooru_25mm_mesh_study/` | Three completed published-geometry meshes, equilibrium gates and experimental/mesh response curves |
| `audit_umat.py`, `UMAT_GUIDE.md`, `reproducibility/umat_audit/` | 712 actual UMAT comparisons, student walkthrough and tested material-point outputs |
| `verify_paper_figures.py`, `reproducibility/figure_replay/` | Pixel-verified reconstruction of all generated manuscript figures |
| `plot_nooru_proportional.py`, `reproducibility/nooru_proportional/` | Shear and normal response diagnostics with explicit equilibrium-failure markers |
| `reproducibility/abaqus_profile/` | Completed separate software-sampling profile, named assembly/user-library self estimates, exact paired response and scope limits |
| `reproducibility/beginner_entry_check/` | Actual 10,000-step beginner execution; all numerical state/response/snapshot arrays exactly reproduce the benchmark |
| `REPRODUCE.md` | Exact run commands and limitations |

The 3D damage panels illustrate workflows qualitatively. The completed three-mesh pure-tension family with published 25 mm notches supplies quantitative experimental and mesh comparisons; it does not establish general mesh independence. The 2D study compares three controlled meshes. These studies do not establish general mesh independence or a runtime advantage over Abaqus.

The [published-geometry coarse 3D comparison](reproducibility/nooru_25mm_coarse/README.md) uses local gauge control and strict equilibrium. Its 35,917 TET4 elements and 21,828 DOFs reach the full gauge-displacement target in 608 accepted increments, with eight rejected trials and a maximum relative equilibrium residual of 8.917e-7. The peak load is 16.6415 kN versus the digitized experimental 19.8529 kN (16.18% below); normalized curve RMS error is 9.27%. Thirty-two local tetrahedron size/direction tests, the compression mapping and eight rotating-direction history checks pass. The separate [illustrative geometry](reproducibility/experimental_3d/README.md) uses 20 mm notches and is not the published 25 mm specimen.


## Size, mesh, CPU and hybrid GPU evidence

See [SCALING_STUDY.md](SCALING_STUDY.md) for all 30 completed configurations, each measured three times (90 runs), response checks, median times, observed ranges, exact meshes and licensed-run/archive-replay commands. Saved MATLAB numerical arrays and Abaqus response CSVs match exactly between observations within each configuration. The [repeat archive](reproducibility/timing_repeats/README.md) preserves the full evidence. The hybrid GPU is functional and retains CPU sparse factorization; no GPU speedup is observed on this workstation. Abaqus SMP reaches a 2.90 speed ratio on the largest mesh. MATLAB load-loop and Abaqus analysis/output times have different scopes.

All three published-geometry pure-tension meshes pass the full-history equilibrium gate. The strict proportional mixed-mode attempt stops at target-bisection exhaustion and remains a documented failure. The beginner-entry execution exactly reproduces the 10,000-step benchmark arrays. The separate Abaqus profile identifies user-library and named assembly self samples, with exact paired numerical responses; complete material/assembly wall-time attribution remains unavailable. See each archive README for its measured scope.


## UMAT and manuscript figure checks

See [UMAT_GUIDE.md](UMAT_GUIDE.md) for the constitutive sequence and secant-tangent limitation. The actual UMAT passes 712 independent material-point comparisons and comparisons with the MATLAB damage functions. Fresh energy/unloading tests and the missing-gradient failure check pass. The tested sources and outputs are archived in `reproducibility/umat_audit/`.

The complete three-mesh 25 mm-notch study is archived in `reproducibility/nooru_25mm_mesh_study/`. All histories reach 0.2 mm gauge displacement within the equilibrium tolerance. Peak underprediction remains 16.18–17.39%; the mesh spread does not explain the experimental discrepancy. The strict mixed-mode failure is preserved in `reproducibility/nooru_proportional_strict/`.

Run `python softwarex/verify_paper_figures.py --workspace C:/runs/figure_replay` from the repository root to rebuild the manuscript figures in a separate folder. All seven generated manuscript assets pass pixel comparison; two supplied geometry illustrations match their archived sources. Runtime and PDF metadata are not numerical reproduction targets.
