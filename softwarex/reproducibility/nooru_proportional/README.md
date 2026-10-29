# Proportional Nooru-Mohamed response diagnostics

The CSV preserves both reaction channels from the 900-increment illustrative
200 x 200 x 50 mm panel with 20 mm-deep, 5 mm-wide notches. The prescribed
relative side displacement reaches 0.30 mm while top displacement reaches
0.50 mm; their ratio is 0.6 throughout. The mesh has 3,933 nodes and 18,927
TET4 elements. The source history and mesh hashes are in `case_description.json`.

## Two response plots

From the repository root, run:

```powershell
python softwarex/plot_nooru_proportional.py
```

The figure shows shear reaction magnitude versus relative side displacement and
signed normal reaction versus top displacement. Recorded values are retained;
no reaction magnitudes or post-peak points are adjusted to resemble experiments.
The solver stores the absolute resultant on the left side as the shear channel.
Red crosses identify sampled increments above the 1e-6 equilibrium tolerance;
the summary reports all failures, including those without a marker.

**894 of 900 recorded increments exceed the equilibrium tolerance.** The maximum
relative residual is 1.0 and the recorded normal-force peak occurs at an
increment above tolerance. This saved metric normalizes by free-node internal
forces (with a 1 N floor), rather than the full reaction scale used in the
strict pure-tension solver; the two residual metrics are not interchangeable.
The curve is a numerical diagnostic, not an equilibrium-verified
response or an experimental validation. The manuscript uses the associated
mixed-mode damage images only as a qualitative workflow illustration.

The solver option name `load_path='4c'` selects this proportional displacement
path; it does not reproduce the sequential force/displacement control of the
published experimental case 4c. No experimental 4a/4c points are overlaid.
The separate published-geometry pure-tension specimen 47-05 comparison is in
[`../nooru_25mm_coarse/`](../nooru_25mm_coarse/README.md) and manuscript Figure 3.

The saved MAT file does not record a complete invocation options structure.
This archive therefore preserves the recorded history for inspection rather
than claiming a fully documented rerun of the illustrative case.
The CSV force, displacement and residual arrays match the saved MAT state
to within 5.1e-11 in absolute value. The state hash and comparison differences
are recorded in `case_description.json`.
