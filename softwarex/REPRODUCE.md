# Reproducing the 2D SoftwareX figures

The 2D MATLAB and Fortran UMAT equivalent-strain invariant has been to `J2 = ((e1-e2)^2 + (e2-e3)^2 + (e3-e1)^2)/6`.

## Environment used

- Windows 11, MATLAB R2024b, base MATLAB, one computational thread.
- Python 3 with NumPy, SciPy, Matplotlib, and Pillow for the plots and 3D figure layouts.
- Abaqus/Standard 2024 with Intel Fortran for the optional UMAT run. Use one Abaqus CPU until its table initialization is made thread-safe.

## MATLAB checks

From `reproducibility/2d` in PowerShell:

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

The solver writes `Gregoire_3PB/results`. The two archived histories in `reproducibility/results_1000` and `reproducibility/results_10000` preserve both runs because running the script again overwrites `results`. The material-point self-test writes `material_energy.csv` with columns `bandwidth_mm, recovered_GF_N_per_mm, relative_error, final_damage`.

New runs also write `matlab_step_diagnostics.csv` with per-step component timings, iteration count, old-damage convergence, and post-damage residual. Set `FRACMATH_CASE_DIR` to a separate mesh folder to avoid overwriting the preserved histories. The preserved 10,000-step run predates this per-step export.

To regenerate the 2D figures from the preserved 10,000-step MATLAB state and Abaqus CSV, run `python plot_verified_figures.py` from the package root after installing NumPy, SciPy, and Matplotlib. The 1,000-step MATLAB history is retained for the increment-sensitivity check in the text but is not plotted in the MATLAB--Abaqus comparison. Figures 4 and 5 use 3D source image panels, recomposed with one enlarged color bar per damage sequence and larger increment labels. Run `python rebuild_3d_figures.py` from the package root to rebuild those layouts from `figure_sources`. The 3D panels are qualitative workflow illustrations.

Run `python compare_solver_diagnostics.py` from this package folder to rebuild `reproducibility/solver_diagnostics.json`. Abaqus `.msg` records solver passes and their elapsed times, but it cannot separate UMAT from assembly and other remaining costs. The different increment histories do not justify a speed ranking.

## Abaqus check

From `reproducibility/abaqus`, run:

```powershell
$env:ABQ_CPUS='1'
$env:ABQ_N_INC='1000'
$env:ABQ_AUTO_PLOT='0'
abaqus cae noGUI=run_3pb_abaqus_OLIVER_T3_FAST.py
```

The Abaqus script rebuilds the geometry/mesh and writes the shape-function gradient table consumed by the UMAT. Review `.sta`, `.msg`, and extracted history CSV before using any Abaqus curve. The Abaqus `maxInc` is `1/ABQ_N_INC` but automatic cutbacks can produce more than that number of accepted increments; the histories need not match the fixed MATLAB step sequence. No Abaqus speed claim is made here.

## Verification scope

The material-point test verifies equivalent-strain mapping, irreversibility, and the exponential law's fracture energy calibration. The structural 3PB results remain load-increment sensitive, and the controlled three-mesh study quantifies sensitivity for one mesh family. The 3D figures illustrate workflows qualitatively.

## Controlled mesh and regularization study

See [`MESH_STUDY.md`](MESH_STUDY.md) for the exact protocol, licensed-run commands, timing scopes, and limitations. The archived study can be analyzed without MATLAB or Abaqus by running `python softwarex/analyze_mesh_study.py` from the repository root.
