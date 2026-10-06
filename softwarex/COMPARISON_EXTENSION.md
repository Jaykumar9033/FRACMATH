# Fixed-increment and formulation comparisons

The current extension archive is `reproducibility/fixed_increment_extension/`. It preserves input/source hashes, actual histories, analysis checks and failure logs. Earlier archives remain unchanged.

## Completed evidence

- Medium/fine MATLAB-Abaqus response comparisons: same exact mesh in each pair, 2,000 fixed increments and -0.1 mm final displacement. Actual ODB times and loading-node displacement are checked.
- Three MATLAB meshes: element-area width `sqrt(2*A)` versus directional Oliver width, with identical material and loading settings within each pair.
- Coarse MATLAB mesh: five equivalent-strain definitions with Oliver width and the same E, nu, ft and GF. Fresh five-driver results are in `reproducibility/equivalent_strain_study/`; the original two-driver extension remains archived.

The suite as a whole is not labelled complete merely because these cases passed. Original baseline/coarse fixed Abaqus failures, the failed baseline smaller-step retry remain explicit; the coarse 4,000-increment comparison is now verified complete.

## Preserved failures and separate retries

The baseline 10,000-increment and coarse 2,000-increment fixed Abaqus jobs failed during convergence. Only their converged history portions are valid response points. The baseline 20,000-increment retry also failed, with 5,174 converged increments (failure during attempt 5,175). Its logs, exact MATLAB reference and frozen source/plan are retained separately in `reproducibility/fixed_increment_retry/`. The coarse 4,000-increment comparison completed and passed exact-mesh, schedule, loading-coverage and finite-history checks. The baseline ODB verifies 5,174 converged increments and final displacement -0.051739998 mm; attempt 5,175 failed.

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

The coarse-mesh CPU study compares five damage drivers: modified von Mises, Mazars, Rankine strain, Rankine stress and smooth Rankine stress. All use the same mesh, 2,000 fixed increments, Oliver width formula, tensile onset and exponential energy calibration. These are scalar-driver alternatives, not complete Mazars or Rankine concrete models. Only modified von Mises uses fc/ft; the compression response differs between the options. See [EQUIVALENT_STRAIN_STUDY.md](EQUIVALENT_STRAIN_STUDY.md) for formulas, checks and reproduction commands.

The two exponential calibrations are worked implementation examples for students and researchers. Following their equations and source code shows how a softening parameter enters the damage update and what must change when another law is implemented. The bending calibration includes elastic and post-peak tensile work; the panel helper calibrates the post-peak contribution. A comparison between these forms requires a common fracture-energy convention. The matched MATLAB-Abaqus bending pairs use the same law and calibration.

## UMAT and performance interpretation

The UMAT loads gradients at synchronized UEXTERNALDB initialization, reads them by element label and evaluates stress without a file read at each material call. It returns a secant stiffness; no consistent damage tangent is claimed. Ten prescribed material examples check its stress, history, damage, width and secant matrix against MATLAB/reference calculations. Separate efficiency diagnostics must retain their timer definitions and overhead limits.

Matching fixed increments does not match equilibrium algorithms or solver-call counts. MATLAB component timers cover the load loop; Abaqus solver time comes from `.msg` and wall time includes analysis/output. Complete Abaqus assembly wall time is not separately allocated.

The native LaTeX flowchart is `figure_sources/damage_update_flowchart.tex`. Current figures are reconstructed by `plot_current_figures.py` and checked by `verify_current_figures.py`. Pure-tension mesh responses and qualitative mixed-mode panel fields remain distinct, with Nooru-Mohamed credited as the benchmark source.

## Smaller fixed-increment verification

The completed coarse 4,000-increment pair has a 0.98% peak difference relative to Abaqus and 0.85% common-CMOD RMS relative to the MATLAB peak. It uses the same exact mesh and -0.1 mm endpoint. See `reproducibility/fixed_increment_retry/final_verification/summary.json` and replay with `verify_fixed_retry.py`. This separate increment refinement does not replace the 2,000-increment three-mesh width study.
