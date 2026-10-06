# FRACMATH study and reproduction package

This folder contains the software companions for the FRACMATH SoftwareX article: study runners, saved histories, source snapshots and figure reconstruction tools. Use the current `main` branch and record the exact commit. Earlier release packages identify archival core versions.

## Study sequence

1. **Material examples:** ten prescribed strain states compare MATLAB, the actual Abaqus UMAT and an independent reference. The permitted difference is `2e-10 + 2e-10 * abs(reference_value)`. These are material-point checks, not one-element structural analyses.
2. **Fixed-increment bending:** medium and fine meshes have completed MATLAB/Abaqus responses at 2,000 fixed increments to -0.1 mm. Each paired comparison uses the exact same mesh. MATLAB and Abaqus still use different nonlinear equilibrium procedures.
3. **Width comparison:** coarse, medium and fine MATLAB responses compare Oliver's directional width with `h = sqrt(2*A)`, where A is each triangle's area. A constant width is not used in the current manuscript plots.
4. **Damage-driver comparison:** The coarse-mesh CPU study compares five damage drivers: modified von Mises, Mazars, Rankine strain, Rankine stress and smooth Rankine stress. All use the same mesh, 2,000 fixed increments, Oliver width formula, tensile onset and exponential energy calibration. These are scalar-driver alternatives, not complete Mazars or Rankine concrete models. Only modified von Mises uses fc/ft; the compression response differs between the options. See [EQUIVALENT_STRAIN_STUDY.md](EQUIVALENT_STRAIN_STUDY.md) for formulas, checks and reproduction commands.
5. **3D MATLAB examples:** the separate pure-tension study checks three-mesh numerical consistency. The mixed-mode panel and torsion fields are qualitative demonstrations. No experimental 3D curve or Abaqus torsion solution is claimed.
6. **Timing:** saved MATLAB load-loop components and separate fixed-increment Abaqus analysis records describe the measured work. Partial UMAT/native profiles do not identify complete assembly wall time.

## Main entry points

| File or folder | Purpose |
| --- | --- |
| `start_here.m` | Medium-mesh, 2,000-step MATLAB example |
| `BEGINNER_GUIDE.md` | Units, array sizes, settings and calculation sequence |
| `reproducibility/2d/` | MATLAB bending solver and supplied inputs |
| `reproducibility/abaqus/` | Abaqus model builder and plane-stress UMAT |
| `reproducibility/material_examples/` | Ten explained material-point examples |
| `reproducibility/fixed_increment_extension/` | Current fixed-increment, area-width and strain-driver records |
| `reproducibility/mesh_study/` | Exact mesh family and optional original study records |
| `reproducibility/nooru_25mm_mesh_study/` | Three pure-tension meshes and histories |
| `reproducibility/nooru_proportional/` | Qualitative mixed-mode panel records |
| `plot_current_figures.py` | Draw current manuscript assets from saved outputs |
| `verify_current_figures.py` | Rebuild and compare those assets in a separate folder |
| `figure_sources/damage_update_flowchart.tex` | Editable native LaTeX/TikZ numerical flowchart |
| `REPRODUCE.md` | Short reproduction workflow |
| `VALIDATION_SCOPE.md` | Supported conclusions and limitations |

## Execution status and archives

The original baseline 10,000-increment and coarse 2,000-increment fixed Abaqus runs stopped during convergence. Their partial histories and logs remain available. The baseline 20,000-increment retry also failed, with 5,174 converged increments (failure during attempt 5,175); its diagnostic logs and exact MATLAB reference are in `reproducibility/fixed_increment_retry/baseline/`. The coarse 4,000-increment comparison completed and passed exact-mesh, schedule, loading-coverage and finite-history checks. There is no adaptive substitution in the current fixed-increment curves.

The larger `umat_audit`/`umat_precision` records, adaptive histories, constant-width controls and repeated scaling timings remain optional archives. They retain their original inputs and counts. The paper's material suite is ten examples. The stopped full sparse GPU experiment is not a complete result; the optional hybrid backend keeps sparse assembly/factorization on the CPU.

Nooru-Mohamed is retained as the panel benchmark source attribution. Descriptive headings distinguish mixed-mode panel fields from pure-tension mesh responses.

See `REPRODUCE.md` for commands and `UMAT_GUIDE.md` for the secant material matrix.
