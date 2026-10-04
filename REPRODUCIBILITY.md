# Reproducing the SoftwareX study

The manuscript, figures, source panels, scripts, and preserved results are in [`softwarex/`](https://github.com/Jaykumar9033/FRACMATH/tree/main/softwarex). The exact study runs are documented in [`softwarex/REPRODUCE.md`](softwarex/REPRODUCE.md). Run commands below from the listed folders because the scripts use relative paths.

## Environment

- Windows 11; MATLAB R2024b Update 6. The preserved increment study uses one computational thread; the hardware study compares one/eight computational-thread limits and a double-precision hybrid GPU backend.
- Abaqus/Standard 2024 with Intel Fortran for the UMAT check. The default uses one Abaqus CPU; ABQ_CPUS=8 selects SMP with eager gradient-table initialization.
- Python 3 with NumPy, SciPy, Matplotlib, and Pillow: `python -m pip install -r requirements.txt`.

## MATLAB 2D notched beam

From `3pb/matlab` in PowerShell:

```powershell
$env:FRACMATH_SELFTEST='1'
matlab -batch "solver_main_3pb"
Remove-Item Env:FRACMATH_SELFTEST

$env:FRACMATH_HEADLESS='1'
$env:FRACMATH_STEPS='1000'
matlab -batch "solver_main_3pb"

$env:FRACMATH_STEPS='10000'
matlab -batch "solver_main_3pb"
```

Each structural run writes `3pb/matlab/Gregoire_3PB/results` and overwrites the previous history. Preserved 1,000- and 10,000-step outputs are in `softwarex/reproducibility/results_1000` and `softwarex/reproducibility/results_10000`. The current `3pb/matlab/Gregoire_3PB/results` CSVs are the 10,000-step run. `FRACMATH_SELFTEST=1` writes `material_energy.csv` in the working folder.

Set `FRACMATH_CASE_DIR` to an absolute path containing the same mesh input files to write a new run outside the preserved case. New runs produce `matlab_step_diagnostics.csv` with iteration counts, old-damage convergence flags, post-damage relative residuals, and the four timed solver components. See [`doc/implementation_walkthrough.md`](doc/implementation_walkthrough.md) for the load-step algorithm and its limitations.

## Abaqus check

From `3pb/abaqus`:

```powershell
$env:ABQ_CPUS='1'
$env:ABQ_N_INC='1000'
$env:ABQ_AUTO_PLOT='0'
abaqus cae noGUI=run_3pb_abaqus_OLIVER_T3_FAST.py
```

The builder writes `oliver_t3_gradN.dat`; the UMAT reads it by element label. Check the new `.sta`, `.msg`, and extracted CSV before comparing runs. Abaqus may cut back increments, so `ABQ_N_INC=1000` does not enforce a fixed 1,000-increment history. The preserved Abaqus CSV, damage fields, and diagnostics are in `softwarex/reproducibility/abaqus/Gregoire_3PB`.

Run `python softwarex/compare_solver_diagnostics.py` from the repository root to produce `softwarex/reproducibility/solver_diagnostics.json` from the preserved MATLAB timer and Abaqus `.msg`. The remaining Abaqus wall time cannot be assigned solely to UMAT or stiffness assembly.

## Figures and limitations

From `softwarex`, run `python plot_verified_figures.py` to rebuild the 2D load and damage figures from the preserved data. Figure 1 uses the preserved 10,000-step MATLAB response. Run `python rebuild_3d_figures.py` to recompose the archived 3D panels with their single shared color bars. The quantitative coarse 3D comparison uses the published 25 mm notch geometry; the illustrative archive uses 20 mm notches. General 3D mesh independence is unverified. Material-point tests check constitutive calibration and history, not structural mesh objectivity. The Abaqus timing record does not isolate UMAT and assembly time, so the repository does not claim MATLAB is faster than Abaqus.

Cite the immutable source and data commit specified in the manuscript.

## Controlled mesh and regularization study

See [`softwarex/MESH_STUDY.md`](softwarex/MESH_STUDY.md) for the exact protocol, licensed-run commands, timing scopes, and limitations. The archived study can be analyzed without MATLAB or Abaqus by running `python softwarex/analyze_mesh_study.py` from the repository root.

## 3D pure-tension experimental comparison

The completed coarse case is preserved in [`softwarex/reproducibility/nooru_25mm_coarse/`](softwarex/reproducibility/nooru_25mm_coarse/README.md). It uses the published 200 × 200 × 50 mm specimen with 25 mm-deep, 5 mm-wide notches and four local gauges. Its 35,917 TET4 elements and 21,828 DOFs reach the complete 0.20 mm mean gauge-displacement target in 608 accepted increments, with eight rejected trials and a maximum accepted relative equilibrium residual of 8.917e-7. The computed peak is 16.6415 kN versus the digitized experimental 19.8529 kN (16.18% below); normalized curve RMS error is 9.27%. See the archive README for source hashes, mesh, inputs, histories, residual checks, experimental source and digitization limits.

The local 3D check passes 32 tetrahedron size/direction cases, the compression mapping and eight rotating-direction damage-history cases. Post-peak fracture-energy calibration and retained damage history are tested explicitly. These local checks do not establish a structural mesh-convergence result. The medium/fine 3D cases remain pending.

The scripts `run_nooru_tension.py` and `analyze_nooru_tension.py` reproduce the separate 20 mm-notch illustrative geometry described in `softwarex/reproducibility/experimental_3d/README.md`; that geometry is distinct from the published 25 mm specimen. Both pure-tension tests are separate from the proportional mixed-mode damage images. The end-twist example does not supply a valid experimental CMOD measurement.

## Size, mesh, CPU and hybrid GPU evidence

See [SCALING_STUDY.md](softwarex/SCALING_STUDY.md) for 30 completed configurations with three sequential observations each (90 runs), response checks, median times, observed ranges, exact meshes and licensed-run/archive-replay commands. The [repeat archive](softwarex/reproducibility/timing_repeats/README.md) preserves both additional observations and the aggregate analysis; the original observation is in `softwarex/reproducibility/scaling_study/`. Saved MATLAB numerical arrays and Abaqus response CSVs match exactly across observations within each configuration. Runtime and image file headers are not expected to match exactly.

The hybrid GPU is functional and retains CPU sparse factorization; no GPU speedup is observed on this workstation. Abaqus SMP reaches a 2.90 speed ratio on the largest mesh. MATLAB load-loop and Abaqus analysis/output times have different scopes, and three workstation observations do not establish statistical confidence intervals. The [separate profile](softwarex/reproducibility/abaqus_profile/README.md) supplies named assembly and user-library self estimates, while complete phase wall-time attribution remains unavailable. The [beginner-entry 10,000-step check](softwarex/reproducibility/beginner_entry_check/README.md) exactly reproduces the preserved numerical arrays.


## UMAT and manuscript figure checks

See [UMAT_GUIDE.md](softwarex/UMAT_GUIDE.md) for the constitutive sequence and secant-tangent limitation. The actual UMAT passes 712 independent material-point comparisons and comparisons with the MATLAB damage functions. Fresh energy/unloading tests and the missing-gradient failure check pass. The tested sources and outputs are archived in `softwarex/reproducibility/umat_audit/`.

The complete three-mesh 25 mm-notch study is archived in `softwarex/reproducibility/nooru_25mm_mesh_study/`. All histories reach 0.2 mm gauge displacement within the equilibrium tolerance. Peak underprediction remains 16.18–17.39%; the mesh spread does not explain the experimental discrepancy. The strict mixed-mode failure is preserved in `softwarex/reproducibility/nooru_proportional_strict/`.

Run `python softwarex/verify_paper_figures.py --workspace C:/runs/figure_replay` from the repository root to rebuild the manuscript figures in a separate folder. All seven generated manuscript assets pass pixel comparison; two supplied geometry illustrations match their archived sources. Runtime and PDF metadata are not numerical reproduction targets.
