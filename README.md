# FRACMATH

FRACMATH is a vectorized MATLAB finite-element implementation of scalar continuum damage with direction-dependent Oliver crack-band regularization. The current repository accompanies a **SoftwareX manuscript in preparation** by Jaykumar Mavani and Madura Pathirage (University of New Mexico). It presents an inspectable implementation of established methods, not a new constitutive model.

## Start here

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

The material-point test checks tensile/compressive equivalent strain, damage irreversibility, Oliver width, and fracture-energy calibration for widths of 0.5, 1, 2, and 4 mm. The 3D pure-tension case compares a nominal-mesh simulation with digitized Nooru-Mohamed specimen 47-05 data. The mixed-mode and torsion panels illustrate damage workflows with shared color bars; their loading controls differ from the experiments. See [experimental comparison](softwarex/reproducibility/experimental_3d/README.md).

## Run

Use MATLAB R2024b or a compatible release for the 2D script. From `3pb/matlab`, run `solver_main_3pb`. Set `FRACMATH_HEADLESS=1` to omit live figures and video; set `FRACMATH_STEPS=1000` or `10000` to select the run length. Set `FRACMATH_SELFTEST=1` to run the material-point check.

From `3pb/abaqus`, run `abaqus cae noGUI=run_3pb_abaqus_OLIVER_T3_FAST.py` with Abaqus/Standard 2024 and a configured Intel Fortran compiler. Set `ABQ_CPUS=1`: the current UMAT table reader has not been made thread-safe for multiple Abaqus workers.

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

See [SCALING_STUDY.md](softwarex/SCALING_STUDY.md) for the 30-case protocol, exact size/mesh choices, pilot checks, licensed-run commands, and timing scopes. Hardware acceleration is evaluated from measured, response-checked runs.

All 30 configurations complete and pass the hardware-response checks. The largest mesh has 100,104 elements and 101,088 DOFs. MATLAB CPU8 and hybrid GPU are slower than CPU1 on this workstation; Abaqus CPU8 reaches a 2.90 speed ratio on the largest mesh. Full measured times and interpretation are in the study guide.
