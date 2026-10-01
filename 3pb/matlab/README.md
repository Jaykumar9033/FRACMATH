# MATLAB 2D 3PB solver

This folder contains the MATLAB implementation of the 2D notched three-point bending continuum damage benchmark.

## Main file to run

```matlab
solver_main_3pb
```

Run it from this folder:

```text
3pb/matlab
```

## Step-by-step

1. Open MATLAB.
2. Change the current folder to `3pb/matlab`.
3. Run:

   ```matlab
   solver_main_3pb
   ```

4. Wait for the solver to finish the displacement-control load steps.
5. Inspect the result folder:

   ```text
   Gregoire_3PB/results
   ```

## Required inputs

The solver expects these files in `Gregoire_3PB/`:

- `nodes.txt`
- `elements.txt`
- `top_nodes.txt`
- `left_nodes.txt`
- `right_nodes.txt`
- `cmod1.txt`
- `cmod2.txt`

## Main outputs

| File | Meaning |
| --- | --- |
| `Gregoire_3PB/results/matlab_load_cmod.csv` | CMOD and load response |
| `Gregoire_3PB/results/matlab_timing.txt` | Timing and peak-load information |
| `Gregoire_3PB/results/matlab_step_diagnostics.csv` | Per-step timing, iteration count, and post-damage residual (new runs) |
| `Gregoire_3PB/results/matlab_oliver_bandwidth_history.csv` | Oliver bandwidth history |
| `../../softwarex/figures/load_cmod_verified.png` | Verified response figure, generated from preserved result states |

## Notes

- The solver uses the modified von Mises equivalent strain, exponential softening, and direction-dependent Oliver crack-band regularization.
- The default material and solver parameters are defined near the top of `solver_main_3pb.m`.
- Keep the working folder at `3pb/matlab` because paths are relative.
- Set `FRACMATH_SELFTEST=1` for the material-point energy check, `FRACMATH_HEADLESS=1` for no live figure/video, and `FRACMATH_STEPS=1000` or `10000` for step count.
- A new run overwrites `Gregoire_3PB/results`. Preserved 1,000- and 10,000-step histories are in `softwarex/reproducibility/`.
- The solver equilibrates the old damage state and updates damage once per load step. Its reported post-update free-DOF residual is nonzero, so the 1,000- and 10,000-step curves differ.
- Set `FRACMATH_CASE_DIR` to another mesh folder to keep the preserved case outputs untouched. The [implementation walkthrough](../../doc/implementation_walkthrough.md) maps each load-step stage to the functions in the solver.
