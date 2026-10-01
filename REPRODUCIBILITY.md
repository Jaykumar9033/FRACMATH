# Reproducing the SoftwareX study

The manuscript, figures, source panels, scripts, and preserved results are in [`softwarex/`](https://github.com/Jaykumar9033/FRACMATH/tree/main/softwarex). The exact study runs are documented in [`softwarex/REPRODUCE.md`](softwarex/REPRODUCE.md). Run commands below from the listed folders because the scripts use relative paths.

## Environment

- Windows 11; MATLAB R2024b, base MATLAB, one computational thread for the reported 2D runs.
- Abaqus/Standard 2024 with Intel Fortran for the UMAT check. Use one Abaqus CPU until gradient-table initialization is thread-safe.
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

From `softwarex`, run `python plot_verified_figures.py` to rebuild the 2D load, timing, and damage figures from the preserved data. Run `python rebuild_3d_figures.py` to recompose the archived 3D panels with their single shared color bars. Quantitative 3D validation is outside the study scope. The material-point test checks constitutive calibration, not structural mesh objectivity. The Abaqus timing record does not isolate UMAT and assembly time, so the repository does not claim MATLAB is faster than Abaqus.

Cite the immutable source and data commit specified in the manuscript.

## Controlled mesh and regularization study

See [`softwarex/MESH_STUDY.md`](softwarex/MESH_STUDY.md) for the exact protocol, licensed-run commands, timing scopes, and limitations. The archived study can be analyzed without MATLAB or Abaqus by running `python softwarex/analyze_mesh_study.py` from the repository root.
