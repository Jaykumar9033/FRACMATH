# Fixed-increment and formulation comparisons

The current extension archive is `reproducibility/fixed_increment_extension/`. It preserves input/source hashes, actual histories, analysis checks and failure logs. Earlier archives remain unchanged.

## Completed evidence

- Medium/fine MATLAB-Abaqus response comparisons: same exact mesh in each pair, 2,000 fixed increments and -0.1 mm final displacement. Actual ODB times and loading-node displacement are checked.
- Three MATLAB meshes: element-area width `sqrt(2*A)` versus directional Oliver width, with identical material and loading settings within each pair.
- Coarse MATLAB mesh: maximum-positive-principal versus modified von Mises equivalent strain, with Oliver width and the same E, nu, ft and GF.

The suite as a whole is not labelled complete merely because these cases passed. Original baseline/coarse fixed Abaqus failures, the failed baseline smaller-step retry and the running coarse retry remain explicit.

## Preserved failures and separate retries

The baseline 10,000-increment and coarse 2,000-increment fixed Abaqus jobs failed during convergence. Only their converged history portions are valid response points. The baseline 20,000-increment retry also failed, with 5,175 accepted increments recorded in `.sta`. Its logs, exact MATLAB reference and frozen source/plan are retained separately in `reproducibility/fixed_increment_retry/`. The coarse 4,000-increment retry is running and needs final schedule, loading coverage and finite-output checks before use as a full paired curve. The reported accepted count is a log diagnostic; no unverified ODB loading displacement is inferred from it.

Fixed increments are retained. There is no automatic adaptive replacement and no NO STOP override to accept unconverged increments. MATLAB can record a complete history while retaining a post-update force residual; it does not use Abaqus's equilibrium algorithm.

## Fresh sequential run

From the repository root, prepare an empty workspace using the preserved coarse/medium/fine mesh sources:

```powershell
python softwarex/run_comparison_extension.py --workspace C:/runs/fixed_extension --cases coarse medium fine --mesh-steps 2000 --stage prepare
```

Inspect `plan.json` and the recorded source/input hashes, then run stages sequentially:

```powershell
python softwarex/run_comparison_extension.py --workspace C:/runs/fixed_extension --cases coarse medium fine --stage abaqus
python softwarex/run_comparison_extension.py --workspace C:/runs/fixed_extension --cases coarse medium fine --stage matlab
python softwarex/run_comparison_extension.py --workspace C:/runs/fixed_extension --cases coarse medium fine --stage analyze
```

Preparation alone does not execute a solver. Exact Oliver references are copied with provenance. Baseline preparation additionally needs its separate preserved source through `--rerun-root`; the short command above omits it.

## Material options

`FRACMATH_REGULARIZATION=area` selects elementwise `sqrt(2*A)`; `oliver` selects directional width. The historical `fixed` option remains only for reproducing old records.

`FRACMATH_EQUIVALENT_STRAIN=rankine` selects the largest positive principal strain, including the plane-stress out-of-plane component. The default is `modified_mises`. Rankine changes the multiaxial damage surface and does not use fc/ft. The coarse peak increases by 11.63% relative to modified von Mises; this is not evidence of greater physical accuracy.

The bending exponential calibration accounts for total uniaxial work, including the elastic contribution. The panel helper uses its separately documented post-onset calibration. They are reported as distinct conventions with their own input settings, not as interchangeable parameter values.

## UMAT and performance interpretation

The UMAT loads gradients at synchronized UEXTERNALDB initialization, reads them by element label and evaluates stress without a file read at each material call. It returns a secant stiffness; no consistent damage tangent is claimed. Ten prescribed material examples check its stress, history, damage, width and secant matrix against MATLAB/reference calculations. Separate efficiency diagnostics must retain their timer definitions and overhead limits.

Matching fixed increments does not match equilibrium algorithms or solver-call counts. MATLAB component timers cover the load loop; Abaqus solver time comes from `.msg` and wall time includes analysis/output. Complete Abaqus assembly wall time is not separately allocated.

The native LaTeX flowchart is `figure_sources/damage_update_flowchart.tex`. Current figures are reconstructed by `plot_current_figures.py` and checked by `verify_current_figures.py`. Pure-tension mesh responses and qualitative mixed-mode panel fields remain distinct, with Nooru-Mohamed credited as the benchmark source.
