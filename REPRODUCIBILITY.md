# Reproducing the FRACMATH study

The current manuscript reports material-point verification, 2D cross-code and mesh-response studies, 3D MATLAB numerical examples and CPU/GPU/SMP timing observations. [softwarex/REPRODUCE.md](softwarex/REPRODUCE.md) provides detailed commands and archive locations. Read [VALIDATION_SCOPE.md](softwarex/VALIDATION_SCOPE.md) before interpreting the comparisons.

## Environment

- MATLAB R2024b on Windows 11 for the recorded structural runs.
- Parallel Computing Toolbox and a supported GPU for the optional hybrid backend.
- Abaqus/Standard 2024 and configured Intel Fortran for Abaqus runs.
- Python plotting dependencies: `python -m pip install -r requirements.txt`.
- Poppler's `pdftoppm` on PATH for PDF pixel comparison.

## First MATLAB run

Open `softwarex/start_here.m` and press Run. It uses the supplied benchmark mesh and writes to `softwarex/student_results` without overwriting the archive. Figure 1 uses 10,000 displacement steps. Set `show_figures = false` for a headless run. Units and array sizes are explained in [BEGINNER_GUIDE.md](softwarex/BEGINNER_GUIDE.md).

For a direct run from `3pb/matlab`:

```powershell
$env:FRACMATH_HEADLESS='1'
$env:FRACMATH_STEPS='10000'
matlab -batch "solver_main_3pb"
```

## Abaqus benchmark

From `3pb/abaqus`, run:

```powershell
$env:ABQ_CPUS='1'
abaqus cae noGUI=run_3pb_abaqus_OLIVER_T3_FAST.py
```

Set `ABQ_CPUS=8` for the SMP case. The builder initializes the Oliver gradient table before material calls. See [UMAT_GUIDE.md](softwarex/UMAT_GUIDE.md) for material states and the secant-matrix limitation.

## Reconstruct figures without licensed solvers

From the repository root:

```powershell
python softwarex/verify_paper_figures.py --workspace C:/runs/fracmath_figures
```

This rebuilds eight generated assets and checks two supplied geometry illustrations. Figure 3 contains the controlled 2D mesh curves; Figure 4 combines the 3D numerical tension curves and qualitative mixed-mode fields; Figure 5 is the MATLAB torsion example; Figure 6 presents the timing observations.

## Further numerical studies

[MESH_STUDY.md](softwarex/MESH_STUDY.md) describes exact paired 2D meshes and Oliver/constant-width controls. [SCALING_STUDY.md](softwarex/SCALING_STUDY.md) describes 30 configurations with three observations each. The three-mesh pure-tension archive is `softwarex/reproducibility/nooru_25mm_mesh_study/`.

The paper uses ten explained material-point examples in `softwarex/reproducibility/material_examples/`, one state for each selected case. Larger developer audits and batch timings remain optional archival records. Other archived energy and experimental diagnostics are retained for traceability but are not current manuscript conclusions. Do not treat material-point checks as a one-element structural test or numerical mesh agreement as physical validation.

## Timing interpretation

MATLAB records assembly, factorization, damage and solve scopes. Abaqus reports sparse-solver timings and iteration counts. Separate UMAT timers and native profiles are documented in [ABAQUS_TIMING_SCOPE.md](softwarex/ABAQUS_TIMING_SCOPE.md). They do not provide complete Abaqus assembly wall time. Different solution histories and timing boundaries prevent a controlled cross-program speed ranking.

## Numerical equality

Compare response and state arrays using the recorded settings. Runtime, file timestamps and PDF metadata are not exact reproduction targets. CPU/GPU agreement is tolerance-based; within-setting repeated arrays are checked separately for exact equality.
