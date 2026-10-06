# Reproducing the FRACMATH study

The current manuscript uses ten material examples, completed fixed-increment MATLAB-Abaqus bending comparisons, an element-area/Oliver width study, a five-driver CPU equivalent-strain comparison, and MATLAB panel/torsion examples. [softwarex/REPRODUCE.md](softwarex/REPRODUCE.md) gives the detailed sequence. [VALIDATION_SCOPE.md](softwarex/VALIDATION_SCOPE.md) explains the limits.

## Environment

- MATLAB R2024b on Windows 11 for the recorded structural runs.
- Parallel Computing Toolbox and a supported GPU for the optional hybrid backend.
- Abaqus/Standard 2024 and configured Intel Fortran for Abaqus runs.
- Python dependencies: `python -m pip install -r requirements.txt`.
- TeX with TikZ for the native flowchart, and Poppler `pdftoppm` for PDF image comparison.

## First MATLAB run

Open `softwarex/start_here.m` and press Run. The supplied medium mesh uses 2,000 fixed increments to a final prescribed displacement of -0.1 mm, Oliver width, modified von Mises equivalent strain and one CPU thread. It writes to `softwarex/student_results`. Set `show_figures = false` for a headless run.

The bare solver in `3pb/matlab` has separate historical defaults. Use `start_here.m` or the study runner to select the current manuscript mesh and settings explicitly.

## Current figure reconstruction

From the repository root:

```powershell
python softwarex/plot_current_figures.py --output C:/runs/current_figures
python softwarex/verify_current_figures.py --workspace C:/runs/current_figure_check
```

The figure scripts read the fixed-increment extension, the five-driver equivalent-strain archive and the supplied 3D figure sources. They do not solve the model. The native damage-update flowchart is in `softwarex/figure_sources/damage_update_flowchart.tex`.

## Material examples

```powershell
python softwarex/run_material_examples.py --workspace softwarex/reproducibility/material_examples --check
```

This rechecks the ten saved states. Fresh compilation and MATLAB execution require an empty output folder and the software listed above; omit `--check` for that workflow. Larger material audits remain optional historical records.

## Fixed-increment structural studies

[COMPARISON_EXTENSION.md](softwarex/COMPARISON_EXTENSION.md) documents preparation and sequential execution. The completed medium/fine Abaqus cases and their MATLAB references use the same exact mesh, 2,000 fixed increments and final displacement of -0.1 mm. The builder sets `ABQ_INCREMENT_MODE=fixed`; unconverged points are not accepted through a NO STOP override.

Original fixed baseline/coarse failures are retained. The baseline 20,000-increment retry also failed after 5,174 converged increments (failure during attempt 5,175); its diagnostic record is `softwarex/reproducibility/fixed_increment_retry/baseline/`. The coarse 4,000-increment comparison completed and passed exact-mesh, schedule, loading-coverage and finite-history checks. Failed fixed jobs are not replaced with adaptive histories. [MESH_STUDY.md](softwarex/MESH_STUDY.md) covers the three-mesh `sqrt(2*A)`/Oliver comparison.

## 3D examples

The three-mesh pure-tension archive is `softwarex/reproducibility/nooru_25mm_mesh_study/`. It supports numerical mesh consistency. The mixed-mode panel and imposed-twist torsion fields are qualitative demonstrations. No experimental 3D curve or Abaqus torsion response is claimed. Nooru-Mohamed remains the benchmark author attribution.

## Timing interpretation

MATLAB measures assembly, factorization, backsolve, damage and remaining load-loop work. Abaqus `.msg` gives combined sparse-solver time and solution counts. The remainder of the Abaqus wall time is not assembly alone. MATLAB values are saved reference observations; the fixed-increment Abaqus timings are separate fresh observations and include analysis/output.

Separate material-call timers and native profiles are described in [ABAQUS_TIMING_SCOPE.md](softwarex/ABAQUS_TIMING_SCOPE.md). They do not provide complete Abaqus assembly wall time. Earlier repeated hardware observations are retained as optional records; no full sparse GPU result is claimed.

## Numerical equality

Use the recorded mesh, material law, increment schedule and backend when comparing arrays. Check finite histories, prescribed displacement coverage and post-update residuals. Matching increment counts does not imply matching nonlinear equilibrium accuracy. Runtime, timestamps and PDF metadata are not exact reproduction targets. CPU/GPU comparisons use tolerances rather than a promise of bit-for-bit equality.

## Five equivalent-strain definitions

[The study guide](softwarex/EQUIVALENT_STRAIN_STUDY.md) describes modified von Mises, Mazars, elastic energy, Rankine stress and smooth Rankine stress. Fresh runs use one exact coarse mesh, Oliver width and 2,000 fixed increments. The UMAT and hybrid GPU kernel retain the default modified-von-Mises definition.
