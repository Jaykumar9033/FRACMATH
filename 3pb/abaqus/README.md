# Abaqus/UMAT 2D 3PB workflow

This folder contains the Abaqus/Standard validation workflow for the same notched 3PB benchmark used by the MATLAB solver.

## Main command

Run from this folder:

```text
3pb/abaqus
```

Command:

```bash
abaqus cae noGUI=run_3pb_abaqus_OLIVER_T3_FAST.py
```

## What the workflow does

1. Builds the 2D CPS3 Abaqus model.
2. Writes the Oliver T3 gradient table used by the UMAT.
3. Compiles and runs `cdm_umat_2d_OLIVER_T3_FAST.for`.
4. Extracts load-CMOD and damage information from the ODB.
5. Writes result CSV files and damage figures.

## Important files

| File or folder | Purpose |
| --- | --- |
| `run_3pb_abaqus_OLIVER_T3_FAST.py` | Main Abaqus build-run-extract-plot script |
| `cdm_umat_2d_OLIVER_T3_FAST.for` | Abaqus UMAT source code |
| `extract_damage.py` | Damage extraction helper |
| `extract_peak_omega.py` | Peak-damage extraction helper |
| `Gregoire_3PB/` | Abaqus job folder, ODB, logs, and extracted results |
| `Gregoire_3PB/results/` | Final Abaqus CSV files and figures |

## Optional controls

Set these before running Abaqus if needed:

```bash
set ABQ_CPUS=4
set ABQ_FIELD_FREQ=1
set ABQ_AUTO_PLOT=1
```

Meaning:

- `ABQ_CPUS`: number of Abaqus CPUs/domains.
- `ABQ_FIELD_FREQ`: field-output frequency. Use `1` to capture the same
  peak-load and post-peak crack states as the MATLAB run. Larger values make a
  smaller ODB but may miss the true peak frame.
- `ABQ_AUTO_PLOT`: set to `1` to plot immediately after the run.
- `ABQ_POSTPEAK_CMOD`: CMOD target for the fully cracked/post-peak snapshot.
  Default is `0.30` mm, matching the MATLAB script.
- `ABQ_DAMAGE_THRESHOLD`: crack plotting threshold. Default is `0.99`,
  matching MATLAB's fully damaged element mask.

## Matching the MATLAB crack figures

The MATLAB solver saves:

- `fig_damage_postpeak`: first state after CMOD reaches about `0.30` mm.
- `fig_damage_last_step`: final state.

The Abaqus workflow now matches that reduced damage-figure set by:

- requesting `SDV` field output every increment by default;
- extracting `SDV2` as the damage variable `omega`;
- plotting cracked elements with `omega >= 0.99`;
- writing both `omega_postpeak.csv` and the clearer alias
  `omega_fully_cracked.csv` from the first frame at or after the
  `ABQ_POSTPEAK_CMOD` target.

The UMAT state variables are:

| SDV | Meaning |
| --- | --- |
| `SDV1` | history variable `kappa` |
| `SDV2` | scalar damage `omega` used for crack plots |
| `SDV3` | Oliver direction-dependent crack-band width `h` |
| `SDV4` | Oliver table flag, `1` when the table is used |
| `SDV5` | direct crack mask, `1` when `omega >= 0.99` |

## Main outputs

| File | Meaning |
| --- | --- |
| `Gregoire_3PB/results/abaqus_load_cmod.csv` | Abaqus CMOD and load response |
| `Gregoire_3PB/results/abaqus_timing.txt` | Abaqus timing summary |
| `Gregoire_3PB/results/abaqus_load_cmod_fig.png` | Abaqus load-CMOD plot |
| `Gregoire_3PB/results/abaqus_fig_damage_postpeak.png` | Damage after peak |
| `Gregoire_3PB/results/abaqus_fig_damage_fully_cracked.png` | Alias for the MATLAB-style fully cracked/post-peak snapshot |
| `Gregoire_3PB/results/abaqus_fig_damage_last_step.png` | Final damage state |
| `Gregoire_3PB/Gregoire_3PB.odb` | Abaqus output database, stored through Git LFS |

## Requirements

- Abaqus/CAE and Abaqus/Standard.
- A Fortran compiler configured for Abaqus UMAT compilation.
- Python with `numpy` and `matplotlib` if plotting outside Abaqus Python.
