# Completed 3D pure-tension case

The quantitative case uses the published 200 x 200 x 50 mm Nooru-Mohamed
panel with two 25 mm-deep, 5 mm-wide notches. It contains 35,917 TET4
elements and 21,828 DOFs. The four physical 65 mm gauges are interpolated
from their coordinates; their mean displacement controls loading to 0.2 mm.
The idealized platens use a common top vertical displacement and minimal
lateral pins. Material parameters are E=29,000 MPa, nu=0.2, ft=3 MPa,
GF=0.11 N/mm and fc/ft=10, without parameter fitting.

The 600 initial target intervals give 608 accepted increments and eight
rejected/bisected trials. Only accepted increments commit nondecreasing
equivalent-strain and damage histories. All accepted relative equilibrium
residuals meet 1e-6. The peak is 16.6415 kN versus a digitized experimental
19.8529 kN: 16.18% below. Curve NRMSE over 1,001 equally spaced points from
0 to 0.2 mm is 9.27% of experimental peak. These discrepancies and the
single completed mesh limit the validation claim; no 3D mesh independence
or increment convergence is established.

Experimental values are digitized estimates from specimen 47-05, thesis
Figure 3.16 (printed page 45); the source, coordinate mapping and reading
uncertainty are in `../experimental_3d/experimental_source.json`. The older
20 mm-notch source and outputs in that folder are a separate idealized
geometry. Its numerical curve is not used for the manuscript's quantitative
25 mm comparison.

## Inspect and reproduce

The folder contains the exact mesh and boundary sets, gauge weights,
generated solver, launcher, accepted targets, response CSVs, final state,
completion metadata and logs. `SHA256.json` records preserved file bytes.
Copy this folder to a separate workspace and execute `matlab -batch run_case`
there to rerun the structural case. The `.mat` final state uses MATLAB v7.3.

To verify the archived full history and regenerate the manuscript curve
without a structural solve, run from the repository root:

```powershell
python softwarex/plot_nooru_coarse.py
```

This writes `analysis/summary.json` and the comparison plot. The regenerated
PDF is used as Figure 3b; the mixed-mode and torsion damage panels remain
qualitative, with their shared color bars.

## Local verification

`material_checks/` preserves source-linked MATLAB checks and their console
output. Four tetrahedral edge lengths times eight tensile directions give
32 checks of equivalent strain, principal direction, projected width,
finite-interval post-peak work and fixed-direction unloading. Compression
mapping and eight rotating-direction unloading/history checks also pass.
The 3D post-peak integral is checked against GF*(1-exp(-4)); the integration
ends before the damage cap. This differs from the 2D total-work convention.

To repeat these checks from the repository root:

```powershell
python softwarex/run_3d_material_checks.py --source softwarex/reproducibility/nooru_25mm_coarse/damage_static.m --workspace C:/runs/tet4_material_checks
```

Local checks verify the constitutive implementation; they do not establish
structural mesh convergence. Medium/fine structural runs and separate Abaqus
profiling are not part of this completed evidence package.
