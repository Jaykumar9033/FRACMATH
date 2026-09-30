# Reproducing the revised 2D SoftwareX figures

This package is a revision candidate, not the public FRACMATH `v1.0.0` tag. The 2D MATLAB and Fortran UMAT equivalent-strain invariant has been corrected to `J2 = ((e1-e2)^2 + (e2-e3)^2 + (e3-e1)^2)/6`.

## Environment used

- Windows 11, MATLAB R2024b, base MATLAB, one computational thread.
- Python 3 with NumPy, SciPy, Matplotlib, and Pillow for the revised plots and 3D figure layouts.
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

To regenerate the revised 2D figures from the preserved 10,000-step MATLAB state and Abaqus CSV, run `python plot_verified_figures.py` from the package root after installing NumPy, SciPy, and Matplotlib. The 1,000-step MATLAB history is retained for the increment-sensitivity check in the text but is not plotted in the MATLAB--Abaqus comparison. Figures 4 and 5 use archived earlier source image panels, recomposed with one enlarged color bar per damage sequence and larger increment labels. Run `python rebuild_3d_figures.py` from the package root to rebuild those layouts from `figure_sources`. The underlying 3D numerical cases were not rerun in this revision.

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

The material-point test verifies equivalent-strain mapping, irreversibility, and the exponential law's fracture energy calibration. The structural 3PB results remain load-increment sensitive, and a structural mesh-refinement study has not been performed. The 3D figures illustrate workflows but have not been rerun as part of this revision.
