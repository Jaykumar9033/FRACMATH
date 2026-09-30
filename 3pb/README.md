# 2D three-point bending benchmark

This folder contains the main 2D notched three-point bending validation case
for the SoftwareX manuscript revision.

The benchmark compares:

1. A vectorized MATLAB continuum damage mechanics solver.
2. An Abaqus/Standard model using an Oliver-matched UMAT.
3. Preserved corrected MATLAB and Abaqus results and verified plotting scripts in `../softwarex/`.

## Folder map

| Path | Purpose |
| --- | --- |
| `matlab/` | MATLAB 2D solver, mesh input files, and MATLAB results |
| `abaqus/` | Abaqus model generation, UMAT, ODB extraction, and Abaqus results |
| `../softwarex/` | Corrected comparisons, figures, source panels, and reproduction data |

## Recommended run order

1. Run the MATLAB solver from `3pb/matlab/`.
2. Run the Abaqus/UMAT workflow from `3pb/abaqus/`.
3. Run `python plot_verified_figures.py` from `softwarex/`.

Detailed instructions are in each subfolder README and in the root `REPRODUCIBILITY.md`.

## Main outputs

| Output | Location |
| --- | --- |
| MATLAB load-CMOD curve | `matlab/Gregoire_3PB/results/matlab_load_cmod.csv` |
| Abaqus load-CMOD curve | `abaqus/Gregoire_3PB/results/abaqus_load_cmod.csv` |
| MATLAB timing log | `matlab/Gregoire_3PB/results/matlab_timing.txt` |
| Abaqus timing log | `abaqus/Gregoire_3PB/results/abaqus_timing.txt` |
| Corrected MATLAB/Abaqus comparison | `../softwarex/figures/load_cmod_verified.png` |
| Timing breakdown | `../softwarex/figures/timing_verified.png` |

The earlier Abaqus ODB and comparison plots were removed from current `main`
because they represent the superseded implementation. They remain accessible
through the historical `v1.0.0` tag. No ODB is needed to regenerate the
SoftwareX figures from the preserved extracted CSV files.
