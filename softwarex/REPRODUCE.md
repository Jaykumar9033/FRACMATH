# Reproducing the 2D SoftwareX figures

The 2D MATLAB and Fortran UMAT equivalent-strain invariant is `J2 = ((e1-e2)^2 + (e2-e3)^2 + (e3-e1)^2)/6`.

For a first MATLAB run, open `start_here.m` and press Run. Settings are at the top, and results are written to `student_results`. See [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md) for the numerical sequence and array sizes.

## Environment used

- Windows 11, MATLAB R2024b, base MATLAB, one computational thread.
- Python 3 with NumPy, SciPy, Matplotlib, and Pillow for the plots and 3D figure layouts.
- Abaqus/Standard 2024 with Intel Fortran for the optional UMAT run. The default uses one Abaqus CPU; ABQ_CPUS=8 selects SMP with eager gradient-table initialization.

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

The solver writes `matlab_step_diagnostics.csv` with per-step component timings, iteration count, old-damage convergence, and post-damage residual. Set `FRACMATH_RESULTS_DIR` to a separate results folder. The 10,000-step archive supplies aggregate timing and numerical states; the mesh and hardware studies also supply per-step diagnostics.

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

The actual 10,000-step beginner execution is preserved in
`reproducibility/beginner_entry_check/`. Run
`python softwarex/analyze_beginner_entry.py --workspace softwarex/reproducibility/beginner_entry_check`
from the repository root to verify exact equality of every state/response and
peak/post-peak snapshot array with the preserved benchmark.

The separate software-sampling profile is in `reproducibility/abaqus_profile/`.
Its README gives archive-replay and fresh-collection commands. Named assembly
and user-library self estimates exclude callees and cannot allocate the
benchmark's unmeasured material/assembly wall-time remainder.

See [`MESH_STUDY.md`](MESH_STUDY.md) for the exact protocol, licensed-run commands, timing scopes, and limitations. The archived study can be analyzed without MATLAB or Abaqus by running `python softwarex/analyze_mesh_study.py` from the repository root.

## 3D pure-tension experimental comparison

For the separate proportional mixed-mode history, run
`python softwarex/plot_nooru_proportional.py` from the repository root.
The two panels preserve shear and normal reaction signs and identify
equilibrium failures. This history is diagnostic: 894 of 900 saved increments
exceed the 1e-6 tolerance. The proportional `4c` option does not reproduce
the published sequential experimental loading, so no 4a/4c experimental
points are overlaid. See `reproducibility/nooru_proportional/README.md`.

Run `python softwarex/analyze_nooru_mesh_study.py --workspace softwarex/reproducibility/nooru_25mm_mesh_study --require-all` from the repository root to check all three completed 25 mm-notch histories and regenerate Figure 4b. `plot_nooru_coarse.py` retains the separate individual coarse-case plot. Copy `softwarex/reproducibility/nooru_25mm_coarse` to a separate workspace and run `matlab -batch run_case` there for a structural rerun. See that folder's README for the mesh, gauge control, source-linked material checks, parameters and validation scope. The experimental source and digitization uncertainty are in `softwarex/reproducibility/experimental_3d/experimental_source.json`. The 20 mm-notch source and histories in that separate folder are idealized-geometry evidence. The proportional mixed-mode damage images and end-twist example remain qualitative.

## Size, mesh, CPU and hybrid GPU evidence

See [SCALING_STUDY.md](SCALING_STUDY.md) for all 30 completed configurations, response checks, measured times, exact meshes and licensed-run/archive-replay commands. The hybrid GPU is functional and retains CPU sparse factorization; no GPU speedup is observed on this workstation. Abaqus SMP reaches a 2.90 speed ratio on the largest mesh.


## UMAT and manuscript figure checks

See [UMAT_GUIDE.md](UMAT_GUIDE.md) for the constitutive sequence and secant-tangent limitation. The actual UMAT passes 712 independent material-point comparisons and comparisons with the MATLAB damage functions. Fresh energy/unloading tests and the missing-gradient failure check pass. The tested sources and outputs are archived in `reproducibility/umat_audit/`.

The complete three-mesh 25 mm-notch study is archived in `reproducibility/nooru_25mm_mesh_study/`. All histories reach 0.2 mm gauge displacement within the equilibrium tolerance. Peak underprediction remains 16.18–17.39%; the mesh spread does not explain the experimental discrepancy. The strict mixed-mode failure is preserved in `reproducibility/nooru_proportional_strict/`.

Run `python softwarex/verify_paper_figures.py --workspace C:/runs/figure_replay` from the repository root to rebuild the manuscript figures in a separate folder. All eight generated assets pass pixel comparison; two supplied geometry illustrations match their archived sources. Runtime and PDF metadata are not numerical reproduction targets.
