# Controlled mesh and regularization study

## Scope

The study uses one 2D notched-beam geometry and three unstructured CPS3
meshes. Abaqus exports the exact node coordinates, connectivity, support sets,
loading set, and CMOD sets used by MATLAB. Supports remain at x=50 and 300 mm;
the prescribed displacement acts on the same 6.25 mm strip at the top centre.
The family has 14,313 / 25,042 / 56,216 elements and 14,686 / 25,534 / 56,954 DOFs.
It is a distinct controlled family from the single-mesh increment study.

The main runs use -0.1 mm prescribed displacement in 2,000 MATLAB steps.
The Abaqus maximum increment is 1/2,000 of the loading step; it may cut back.
Both material calibrations on all three meshes also use 4,000 steps to quantify increment sensitivity.

## Regularization control and energy

The `oliver` runs recompute the projected element width and rescale the
exponential softening law. The `fixed` runs use a reference calibration width
of 1.25 mm for all elements on all meshes, so their local stress–strain law
does not change with mesh size. All other material properties are identical.
The fixed law is an ablation of element-size compensation, not a new model.

MATLAB runs write `matlab_energy_history.csv`. Its damage dissipation is
the positive end-of-step quadrature sum of `Y * delta(omega) * volume`, where
`Y = 0.5 * strain' * D * strain`. External work integrates reaction against
the imposed displacement by the trapezoidal rule. Stored elastic energy is
the volume sum of `(1-omega) * Y`. The difference between work and stored
energy plus dissipation diagnoses increment and equilibrium errors.

The analysis compares dissipation at a common CMOD of 0.10 mm. This is partial
structural dissipation; it is not a direct estimate of complete fracture
energy or a prescribed crack area. The one-element test separately checks
the full stress–strain integral against the fracture-energy calibration.

## Run

Install the repository Python dependencies. MATLAB R2024b and licensed
Abaqus/Standard with a configured Fortran compiler are required. From the
repository root:

```powershell
python softwarex/run_mesh_study.py --workspace C:/fracmath_runs/mesh_study --steps 2000 --increment-checks --fixed-fine-check
```

Stages can be run separately with `--stage build`, `--stage matlab`, and
`--stage abaqus`. On the tested Intel ifx setup, add `--ifx-lowercase` to
generate a local `abaqus_v6.env` symbol-name override. This is specific to
that compiler configuration and should not replace a working site setup.
New runs stay in their own directories; the separate 1,000/10,000-step data
are not overwritten. Heavy simulation jobs run sequentially for timing.

After completion:

```powershell
python softwarex/analyze_mesh_study.py --workspace C:/fracmath_runs/mesh_study
```

For the archived package, `python analyze_mesh_study.py` from the package
folder regenerates the summary JSON/CSVs and the six-panel manuscript figure.
The analysis requires matching history lengths, converged frozen-damage
linear solves, nondecreasing dissipation, the fixed support coordinates, and
the requested common CMOD. It checks that each Abaqus solver timing entry is
accounted for in the `.msg` summary.

## Timing and memory boundaries

MATLAB wall time covers the headless load loop, including energy
diagnostics, but excludes mesh preprocessing and writing final files.
The factorization, assembly, damage, and solve scopes are recorded separately.
MATLAB memory is the operating system's peak process working set and includes
the MATLAB runtime. The older allocation-delta record is not a peak-memory
measurement.

Abaqus wall time comes from its `.msg`; it includes analysis operations and
output. Its sparse-solver timer combines the reported solver passes. The
remaining wall time cannot be partitioned into UMAT, assembly, convergence,
and output from `.msg` alone. `abaqus.sampling.json` records a one-second
sampled maximum working set for `standard.exe` only, excluding CAE; it is a
sampled estimate and has a different process scope from MATLAB memory.

The MATLAB sequential update and Abaqus equilibrium iteration differ.
Report their increment counts, residuals, and timing boundaries together.
These records support inspection of scaling and solver costs; a speed
ranking requires matching accuracy and timing scopes. One mesh family and
one load path do not establish general mesh or orientation independence.

## Mesh design and interpretation

The central 50 mm-wide region containing the notch is refined over the
100 mm beam height. Nominal local seeds are 1.25, 0.9375, and 0.625 mm;
the outer seeds are five times larger. Geometry, support coordinates, loading
strip, material, and final displacement remain fixed. Exact node and element
files are hashed before the Abaqus jobs and checked after rebuilding, so the
code-to-code comparisons use identical meshes.

The refinement series was prescribed before evaluating results. Both peak-load
and dissipation sensitivity are reported, together with smaller-increment
checks. Residual sensitivity is retained in the discussion; meshes are not
selected to hide it.

## Standalone UMAT material test

`umat_material_check.f90` links to the actual unmodified 2D UMAT. It checks
uniaxial tension/compression mapping, four projected widths (including that
the gradient-table path is used), full softening energy, monotone damage,
and partial-damage unload/reload history. Sixteen further cases combine the
four triangle base widths with principal tensile directions of 15, 45, 75,
and 90 degrees, checking analytic projected widths and softening energy.
This verifies local direction handling, not structural orientation independence.
It writes energy and stress�strain
CSVs. Its `GETOUTDIR` stub is only for standalone testing and must not be
linked into an Abaqus job. This tests local material calculations; it does
not test the Abaqus global equilibrium procedure.

From a scratch folder, after initializing Intel Fortran, compile with the
site Abaqus include directory and both sources. On the tested setup:

```powershell
ifx /O2 /extend-source /names:lowercase /include:"C:/SIMULIA/EstProducts/2024/SMAUsubs/PublicInterfaces" C:/path/FRACMATH/3pb/abaqus/cdm_umat_2d_OLIVER_T3_FAST.for C:/path/FRACMATH/softwarex/umat_material_check.f90 /exe:umat_material_check.exe
./umat_material_check.exe
```

The test was run using Intel ifx 2025.0.4. Archived outputs are in
`reproducibility/mesh_study/material_tests`. MATLAB tests additionally exercise
the fixed-law control with the appropriate size-dependent energy target.

The analyzer also inspects saved peak states. In the three main Oliver runs,
all area associated with elements having damage >=0.95 lies inside the
central refinement region (by centroid). The minimum triangle angles in
those elements are 44.2, 49.1, and 37.5 degrees, respectively. These are
localization/mesh diagnostics at each run's peak, not a comparison at an
identical damage state or a claim of converged crack-band geometry.

To repeat the MATLAB material checks from a separate scratch folder:

```powershell
$fracmathRepo='C:/path/FRACMATH'
New-Item -ItemType Directory -Force C:/fracmath_runs/material_tests | Out-Null
Set-Location C:/fracmath_runs/material_tests
$env:FRACMATH_CASE_DIR="$fracmathRepo/softwarex/reproducibility/mesh_study/coarse/mesh"
$env:FRACMATH_RESULTS_DIR='C:/fracmath_runs/material_tests/scratch'
$env:FRACMATH_SELFTEST='1'
$env:FRACMATH_FIXED_WIDTH='1.25'
$env:FRACMATH_REGULARIZATION='oliver'
matlab -batch "addpath('$fracmathRepo/3pb/matlab'); solver_main_3pb"
$env:FRACMATH_REGULARIZATION='fixed'
matlab -batch "addpath('$fracmathRepo/3pb/matlab'); solver_main_3pb"
Remove-Item Env:FRACMATH_SELFTEST,Env:FRACMATH_REGULARIZATION,Env:FRACMATH_FIXED_WIDTH,Env:FRACMATH_CASE_DIR,Env:FRACMATH_RESULTS_DIR
```

MATLAB structural runs can also use the archived `coarse/mesh`, `medium/mesh`,
and `fine/mesh` folders directly through `FRACMATH_CASE_DIR`, with
`FRACMATH_SELFTEST=0`, `FRACMATH_HEADLESS=1`, `FRACMATH_STEPS=2000`,
`FRACMATH_MAX_DISP=-0.1`, and a new `FRACMATH_RESULTS_DIR`. These MATLAB-only
reruns do not require Abaqus; creating new meshes or Abaqus comparisons does.

## Matched smaller-increment family

The fixed-law fine-mesh check showed greater increment sensitivity. The study
therefore includes 4,000-step runs for both calibrations on all three meshes,
to check that the regularization comparison persists at matched smaller
increments. After the main sequence above, fill the three remaining runs:

```powershell
python softwarex/run_mesh_study.py --workspace C:/fracmath_runs/mesh_study --stage matlab --steps 4000 --meshes coarse medium --regularizations oliver fixed
```

Existing complete coarse Oliver results are checked and skipped. The analyzer
reports both main and refined mesh spreads and all six increment changes.
Finite-increment checks are not proof of asymptotic convergence.

In fixed-law runs, the legacy `matlab_oliver_bandwidth_history.csv` filename
and `Oliver h` log labels record the calibration width (1.25 mm), not a
projected width. The `Regularization` log entry and saved `p` settings identify
the selected mode. The source keeps this output name for compatibility.

The archived study data use `.gitattributes -text` to preserve tested bytes
and SHA256 checks across platforms. `source_sha256` records raw tested source
bytes; `source_text_sha256` normalizes line endings because Git may
normalize source-file newlines. The immutable commit identifies the source
version. Individual invocation records retain their original raw-byte hashes.

## Extract an existing Abaqus result

If a successful analysis has an ODB but no response CSV, export it without
submitting another analysis:

```powershell
python softwarex/extract_mesh_study.py --workspace C:/fracmath_runs/mesh_study
```

The extractor checks the successful status file and process-completion record.
The builder also supports `ABQ_EXTRACT_ONLY=1` for an existing job directory.
