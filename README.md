# FRACMATH

FRACMATH is a vectorized MATLAB finite-element implementation of scalar continuum damage with direction-dependent Oliver crack-band regularization. The current repository accompanies a **SoftwareX manuscript in preparation** by Jaykumar Mavani and Madura Pathirage (University of New Mexico). It presents an inspectable implementation of established methods, not a new constitutive model.

## Start here

Students can open [`softwarex/start_here.m`](softwarex/start_here.m) in MATLAB and press Run. The settings are at the top; the supplied mesh and the paper's solver are used directly. Read the [beginner guide](softwarex/BEGINNER_GUIDE.md) for units, array sizes, functions, and output checks.

| Item | Location | Purpose |
| --- | --- | --- |
| 2D MATLAB solver | [`3pb/matlab/solver_main_3pb.m`](3pb/matlab/solver_main_3pb.m) | Notched three-point bending; `FRACMATH_STEPS`, `FRACMATH_HEADLESS`, and `FRACMATH_SELFTEST` controls |
| Abaqus UMAT and job builder | [`3pb/abaqus/`](https://github.com/Jaykumar9033/FRACMATH/tree/main/3pb/abaqus) | Matched material update and Oliver T3 gradient table with eager SMP initialization |
| SoftwareX manuscript and figures | [`softwarex/`](https://github.com/Jaykumar9033/FRACMATH/tree/main/softwarex) | Draft PDF, TeX, figure sources, plotting scripts, and verified data |
| Reproduction instructions | [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) | Commands, environment, checks, and numerical limitations |
| 3D examples | [`Noor mohammad/`](https://github.com/Jaykumar9033/FRACMATH/tree/main/Noor%20mohammad), [`Torsion/`](https://github.com/Jaykumar9033/FRACMATH/tree/main/Torsion) | Qualitative damage-workflow examples |
| Theory manual | [`doc/theory_manual.tex`](doc/theory_manual.tex) | Equations and solver explanation; PDF pending recompilation |
| Implementation walkthrough | [`doc/implementation_walkthrough.md`](doc/implementation_walkthrough.md) | Load-step pseudocode, profiling fields, convergence limit, and larger-mesh protocol |

The MATLAB and Abaqus UMAT implementations use
`J2 = ((e1-e2)^2 + (e2-e3)^2 + (e3-e1)^2)/6`.
The manuscript identifies the source and study data with an immutable Git commit.

## Verified 2D results

The preserved fixed-step MATLAB runs used 1,000 and 10,000 displacement steps. Their peak loads are 4.26464 and 4.02633 kN, respectively. The one-CPU Abaqus run reached 3.99914 kN with 1,136 accepted adaptive increments and 4,817 solver passes. Its 832 s wall time includes more than the 100.2 s summed sparse-solver timer. The distinct step histories and unknown time spent in UMAT, assembly, convergence, and output do not support a speed-ranking claim. These results use one mesh. The controlled study below assesses mesh sensitivity separately.

The material-point test checks tensile/compressive equivalent strain, damage irreversibility, Oliver width, and fracture-energy calibration for widths of 0.5, 1, 2, and 4 mm. The mixed-mode and torsion panels illustrate damage workflows with shared color bars; their loading controls differ from the experiments. The [illustrative 3D comparison](softwarex/reproducibility/experimental_3d/README.md) uses 20 mm notches and is distinct from the published 25 mm specimen geometry described below.

## Run

Use MATLAB R2024b or a compatible release for the 2D script. From `3pb/matlab`, run `solver_main_3pb`. Set `FRACMATH_HEADLESS=1` to omit live figures and video; set `FRACMATH_STEPS=1000` or `10000` to select the run length. Set `FRACMATH_SELFTEST=1` to run the material-point check.

From `3pb/abaqus`, run `abaqus cae noGUI=run_3pb_abaqus_OLIVER_T3_FAST.py` with Abaqus/Standard 2024 and a configured Intel Fortran compiler. Set `ABQ_CPUS=1` for one CPU or `ABQ_CPUS=8` for SMP; the gradient table is initialized before parallel material calls.

From `softwarex`, run `python plot_verified_figures.py` to regenerate the 2D manuscript figures from the preserved result files. Run `python rebuild_3d_figures.py` to recompose the archived 3D panels with shared color bars. Install Python dependencies with `python -m pip install -r requirements.txt` from the repository root. See the [full guide](REPRODUCIBILITY.md) for commands and expected outputs.

From the repository root, run `python softwarex/compare_solver_diagnostics.py` for an inspectable MATLAB/Abaqus timing breakdown. The controlled MATLAB study writes `matlab_step_diagnostics.csv`, including per-step costs and the post-damage residual. The 10,000-step increment-study archive provides aggregate timing; the controlled mesh study also provides per-step diagnostics.

## Citation and license

This repository is MIT licensed. Cite the immutable code commit specified in the SoftwareX manuscript; citation metadata is in [`CITATION.cff`](CITATION.cff).

## Controlled SoftwareX mesh study

Three meshes contain 14,313 / 25,042 / 56,216 elements and
14,686 / 25,534 / 56,954 DOFs. The central notch region is refined;
outer element seeds are five times larger. Support coordinates and loading
strip remain fixed, and exact Abaqus mesh files are exported to MATLAB.

At CMOD 0.10 mm, the three-mesh spread in partial damage dissipation is
6.86% with Oliver regularization versus 18.21% with a fixed stress–strain
law. Peak-load spreads are 6.19% and 6.78%, respectively. These measures
use `(maximum - minimum) / mean`. Regularization improves the dissipation
comparison for this family but does not establish complete mesh independence.
Smaller-increment checks, energy balance, and post-damage residuals qualify
the interpretation. Abaqus job diagnostics qualify the timing comparison.

At 4,000 increments, the dissipation spreads are 6.44% (Oliver) and 20.76% (fixed law). All three Abaqus jobs completed on the identical exported meshes; MATLAB peak loads differ from Abaqus by 1.87%, 2.88%, and 2.78%, respectively.

See [`softwarex/MESH_STUDY.md`](softwarex/MESH_STUDY.md),
[`softwarex/REVIEWER_CHANGES.md`](softwarex/REVIEWER_CHANGES.md), and
[`softwarex/reproducibility/mesh_study/summary.json`](softwarex/reproducibility/mesh_study/summary.json).
To regenerate the study summary and Figure 6 without licensed solvers:

```powershell
python softwarex/analyze_mesh_study.py
```

## CPU and hybrid GPU size/mesh study

The solver supports `FRACMATH_THREADS` (default 1), `FRACMATH_SIZE_SCALE` (default 1), and `FRACMATH_BACKEND=cpu` or `gpu_hybrid` (default cpu). The hybrid backend runs element stiffness values and damage operations on a double-precision GPU and retains CPU sparse assembly/factorization. It requires Parallel Computing Toolbox and a compatible GPU. Abaqus supports SMP after eager gradient-table loading at analysis start.

See [SCALING_STUDY.md](softwarex/SCALING_STUDY.md) for the 30-configuration protocol, exact size/mesh choices, pilot checks, licensed-run commands, and timing scopes. Each configuration has three sequential workstation observations, giving 90 completed runs. Hardware acceleration is evaluated from measured, response-checked runs.

All 30 configurations complete and pass the hardware-response checks. Saved MATLAB numerical arrays and Abaqus response CSVs match exactly across the three observations within each configuration. Median times and observed minimum/maximum ranges are preserved in [timing_repeats](softwarex/reproducibility/timing_repeats/README.md). The largest mesh has 100,104 elements and 101,088 DOFs. MATLAB CPU8 and hybrid GPU are slower than CPU1 for all six median size/mesh comparisons on this workstation; Abaqus CPU8 reaches a 2.90 speed ratio on the largest mesh. MATLAB load-loop time and Abaqus analysis/output time have different scopes, so these totals do not establish a cross-program speed ranking.

## 3D material checks and experimental comparison

The published-geometry pure-tension case uses a 200 × 200 × 50 mm specimen with two 25 mm-deep, 5 mm-wide notches and four local displacement gauges. Its completed coarse mesh contains 35,917 TET4 elements and 21,828 DOFs. The run reaches the final 0.20 mm mean gauge displacement in 608 accepted increments, with eight rejected trials; the maximum accepted relative equilibrium residual is 8.917e-7.

The three meshes predict peaks of 16.6415, 16.3997 and 16.5261 kN versus 19.8529 kN in digitized specimen 47-05: 16.18–17.39% underprediction. Curve NRMSE is 9.09–9.27%. Peak spread is 1.46% and medium/fine RMS difference is 0.35% of fine peak. The [three-mesh archive](softwarex/reproducibility/nooru_25mm_mesh_study/README.md) supplies exact meshes, sources, inputs, histories and full equilibrium checks. These results do not establish general mesh independence.

Local tests pass for 32 tetrahedron-size/direction cases, compression mapping, and eight rotating-direction history cases. They check projected width, tensile response, post-peak energy calibration and irreversibility. The strict proportional mixed-mode attempt terminates at bisection exhaustion and is archived as a failure. The [10,000-step beginner check](softwarex/reproducibility/beginner_entry_check/README.md) exactly reproduces every numerical response, state and snapshot array. A [separate Abaqus profile](softwarex/reproducibility/abaqus_profile/README.md) identifies user-library and named assembly self samples; it does not supply complete phase wall times.


## UMAT and manuscript figure checks

See [UMAT_GUIDE.md](softwarex/UMAT_GUIDE.md) for the constitutive sequence and secant-tangent limitation. The actual UMAT passes 712 independent material-point comparisons and comparisons with the MATLAB damage functions. Fresh energy/unloading tests and the missing-gradient failure check pass. The tested sources and outputs are archived in `softwarex/reproducibility/umat_audit/`.

The complete three-mesh 25 mm-notch study is archived in `softwarex/reproducibility/nooru_25mm_mesh_study/`. All histories reach 0.2 mm gauge displacement within the equilibrium tolerance. Peak underprediction remains 16.18–17.39%; the mesh spread does not explain the experimental discrepancy. The strict mixed-mode failure is preserved in `softwarex/reproducibility/nooru_proportional_strict/`.

Run `python softwarex/verify_paper_figures.py --workspace C:/runs/figure_replay` from the repository root to rebuild the manuscript figures in a separate folder. All eight generated assets pass pixel comparison; two supplied geometry illustrations match their archived sources. Runtime and PDF metadata are not numerical reproduction targets.


## Software release

[FRACMATH v1.1.1](https://github.com/Jaykumar9033/FRACMATH/releases/tag/v1.1.1) is archived at [Zenodo, DOI 10.5281/zenodo.23138595](https://doi.org/10.5281/zenodo.23138595). All 366 archived-file hashes match the tagged Git source. The manuscript identifies this source version and its numerical-validation limits.
