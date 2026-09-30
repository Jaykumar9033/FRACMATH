# Reproducing the SoftwareX revision

The manuscript, figures, source panels, scripts, and preserved results are in [`softwarex/`](softwarex/). The exact revision runs are documented in [`softwarex/REPRODUCE.md`](softwarex/REPRODUCE.md). Run commands below from the listed folders because the scripts use relative paths.

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

Each structural run writes `3pb/matlab/Gregoire_3PB/results` and overwrites the previous history. Preserved 1,000- and 10,000-step outputs are in `softwarex/reproducibility/results_1000` and `softwarex/reproducibility/results_10000`. The current `3pb/matlab/Gregoire_3PB/results` CSVs are the corrected 10,000-step run. `FRACMATH_SELFTEST=1` writes `material_energy.csv` in the working folder.

## Abaqus check

From `3pb/abaqus`:

```powershell
$env:ABQ_CPUS='1'
$env:ABQ_N_INC='1000'
$env:ABQ_AUTO_PLOT='0'
abaqus cae noGUI=run_3pb_abaqus_OLIVER_T3_FAST.py
```

The builder writes `oliver_t3_gradN.dat`; the UMAT reads it by element label. Check the new `.sta`, `.msg`, and extracted CSV before comparing runs. Abaqus may cut back increments, so `ABQ_N_INC=1000` does not enforce a fixed 1,000-increment history. The preserved corrected Abaqus CSV, damage fields, and diagnostics are in `softwarex/reproducibility/abaqus/Gregoire_3PB`.

## Figures and limitations

From `softwarex`, run `python plot_verified_figures.py` to rebuild the 2D load, timing, and damage figures from the preserved corrected data. Run `python rebuild_aes_figures.py` to recompose the archived 3D panels with their single shared color bars. The 3D numerical simulations were not rerun. The material-point test checks constitutive calibration, not structural mesh objectivity. The Abaqus timing record does not isolate UMAT and assembly time, so the repository does not claim MATLAB is faster than Abaqus.

The archived [`v1.0.0`](https://github.com/Jaykumar9033/FRACMATH/tree/v1.0.0) and [Zenodo DOI](https://doi.org/10.5281/zenodo.21297071) are for the earlier implementation. Do not use that DOI as the identifier of the current SoftwareX revision.
