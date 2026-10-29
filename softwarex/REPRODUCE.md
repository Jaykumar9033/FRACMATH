# Reproducing the FRACMATH SoftwareX results

Commands below are run from the repository root. Use fresh folders for numerical runs; keep supplied reference data unchanged.

## 1. First MATLAB run

Open `softwarex/start_here.m` and press Run. It selects the supplied medium mesh, 2,000 fixed increments, -0.1 mm final displacement, Oliver width, modified von Mises equivalent strain and one CPU thread. Outputs are saved separately in `softwarex/student_results`.

Read `BEGINNER_GUIDE.md` before changing a setting. Historical beginner and baseline archives use different schedules and are not the current bending reference.

## 2. Material-point consistency

Recheck the ten saved material examples:

```powershell
python softwarex/run_material_examples.py --workspace softwarex/reproducibility/material_examples --check
```

For fresh compilation and MATLAB evaluation, use an empty workspace:

```powershell
python softwarex/run_material_examples.py --workspace C:/runs/material_examples
```

The source UMAT is compiled without changing its material equations. The comparison includes equivalent strain, history, damage, width, stress and the documented secant stiffness. A checked value passes when its difference is at most `2e-10 + 2e-10 * abs(reference_value)`.

## 3. Reconstruct the current figures

```powershell
python softwarex/plot_current_figures.py --output C:/runs/current_figures
python softwarex/verify_current_figures.py --workspace C:/runs/current_figure_check
```

These scripts use saved outputs rather than running MATLAB or Abaqus. They draw the advanced bending figure, element-area/Oliver comparison, equivalent-strain comparison and current 3D assets. The numerical flowchart is native TikZ source in `softwarex/figure_sources/damage_update_flowchart.tex`.

Figure 4 reconstruction selects two numerical load-CMOD curves and reads the published experimental 100 mm beam trace in [experimental_2d](reproducibility/experimental_2d/README.md). Open markers select recovered graphic vertices. [extract_published_beam_curve.py](extract_published_beam_curve.py) documents their recovery from the native author figure and source checks. These are not raw laboratory samples or points generated from numerical curves. The plot shows CMOD 0–0.16 mm; the full recovered trace extends to 0.3363 mm. Nominal beam dimensions match, but exact experimental notch width, loading control and replicate identity are unverified. No material fitting is performed.

## 4. Prepare and run the structural extension

Abaqus/Standard, configured Intel Fortran and MATLAB are required. Prepare exact preserved mesh cases in an empty workspace:

```powershell
python softwarex/run_comparison_extension.py --workspace C:/runs/fixed_extension --cases coarse medium fine --mesh-steps 2000 --stage prepare
```

Inspect `plan.json`, mesh hashes, final displacement and input schedules before execution. Run each stage sequentially:

```powershell
python softwarex/run_comparison_extension.py --workspace C:/runs/fixed_extension --cases coarse medium fine --stage abaqus
python softwarex/run_comparison_extension.py --workspace C:/runs/fixed_extension --cases coarse medium fine --stage matlab
python softwarex/run_comparison_extension.py --workspace C:/runs/fixed_extension --cases coarse medium fine --stage analyze
```

The runner copies the exact Oliver MATLAB references with provenance; it does not count them as new runs. The MATLAB stage adds three area-width cases and a coarse principal-strain case. The Abaqus stage uses fixed increments and retains normal equilibrium acceptance. A failed job is preserved and is not rerun with adaptive increments. Baseline preparation needs its separate exact preserved input source and is not included in this shortest command.

The completed current cross-code plots use medium/fine, 2,000 increments and -0.1 mm final displacement. Their actual ODB history times and loading-node displacement are checked. The baseline 10,000-step and coarse 2,000-step Abaqus failures are not complete curves. The baseline 20,000-step retry also failed, with 5,174 converged increments (failure during attempt 5,175). Its diagnostic logs and exact MATLAB reference are preserved in `reproducibility/fixed_increment_retry/baseline/`. The coarse 4,000-increment comparison completed and passed exact-mesh, schedule, loading-coverage and finite-history checks.

## 5. Interpret width and equivalent-strain studies

`h = sqrt(2*A)` uses the area of each triangle. Oliver width uses projected shape-function gradients and the maximum-principal-strain direction. All current width-study cases keep the mesh, material, increment count and final displacement fixed within a pair.

For fresh Figure 4 simulations, run `python softwarex/run_equivalent_strain_study.py --workspace C:/runs/strain_study --stage all`. This performs the material checks and the two current structural cases sequentially.

The current coarse-mesh CPU comparison uses two damage drivers: modified von Mises and Rankine stress. Figure 4 shows load versus CMOD. All use the same mesh, 2,000 fixed increments, Oliver width formula, tensile onset and exponential energy calibration. These are scalar-driver alternatives within the same damage update, not complete independently calibrated concrete models. Only modified von Mises uses fc/ft. See [EQUIVALENT_STRAIN_STUDY.md](EQUIVALENT_STRAIN_STUDY.md) for formulas, checks and reproduction commands.

## 6. 3D numerical examples

```powershell
python softwarex/analyze_nooru_mesh_study.py --workspace softwarex/reproducibility/unified_softening_20261014/mesh_study --require-all
```

This checks the three completed pure-tension histories. It is a mesh-consistency/equilibrium check, not experimental validation. The mixed-mode panel archive `reproducibility/nooru_proportional/` supplies qualitative damage illustrations. Its loading and notch geometry differ from the pure-tension case. Preserve Nooru-Mohamed's benchmark attribution.

Torsion fields are generated by the MATLAB workflow. Abaqus torsion files are geometry resources; no Abaqus torsion response is used in the article.

## 7. Timing and numerical limits

MATLAB records load-loop assembly, factorization, backsolve, damage and remaining work. Abaqus reports combined solver time from `.msg`; its remaining wall time includes several types of work and cannot be called assembly alone. Current MATLAB timings are saved reference observations; Abaqus timings are from separate fresh fixed-increment runs and include analysis/output.

Matching fixed increments does not match the nonlinear algorithms. MATLAB records a residual after its damage update; Abaqus converges through equilibrium iterations with a secant material matrix. See `VALIDATION_SCOPE.md` and `ABAQUS_TIMING_SCOPE.md`.

## Submission records

Use the current figure scripts above. Development-only profiles, larger UMAT audits and superseded figure replays are not included. Current reference data, input/source snapshots, convergence diagnostics and the three-observation timing study are retained.

## Updated 3D softening and completed mixed-mode continuation (21 October 2026)

The current Nooru-Mohamed material source uses `eps_f = kappa0/2 + GF/(h*ft)`, with `kappa0 = ft/E`. Here fracture energy includes elastic tensile work before the peak and softening work after it. The pure-tension three-mesh study in `reproducibility/unified_softening_20261014/mesh_study` completed with this convention.

For the corrected mixed-mode case, add `softwarex` to the MATLAB path and run:

```matlab
run_mixed_mode_continuation('C:/runs/fracmath_mixed_mode', true)
```

Choose a fresh writable workspace. The entry point copies the mesh, accepted restart, and tested solver sources there, builds its cache, checks the analytical material tangent, runs opening-controlled continuation to the original final displacement, and repeats with half-size continuation steps when the second argument is true. Subsequent calls resume compatible accepted checkpoints. This is continuation from the supplied converged 126-state prefix, not a newly initialized loading history.

The constitutive width still follows the current principal-strain direction. A fixed local projection is used only as a continuation coordinate; the physical proportional boundary-displacement ratio is retained. The endpoint is imposed exactly. History is committed only after convergence and checked again afterward. The completed reference histories and verification summary are in `reproducibility/unified_softening_20261014/mixed_mode_solver_20261021`.

Both reference runs satisfy the original `1e-6` relative equilibrium tolerance. The largest vertical-force difference between the resumed curves is 0.191% of the force at the restart; the half-step energy-balance mismatch over the resumed path is 0.182%. These are numerical checks of the specified illustrative model, not experimental validation. The earlier fixed-target mixed-mode attempts remain failed attempts and are not relabeled as completed results.
