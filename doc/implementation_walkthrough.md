# Implementation walkthrough for reviewers

The executable 2D implementation is `3pb/matlab/solver_main_3pb.m`. Its
`softwarex/reproducibility/2d/` copy is kept identical for the submission
package. This is a documented implementation of established continuum damage
and Oliver crack-band regularization, not a new constitutive law.

## Load-step algorithm

1. `load_mesh` reads nodes, T3 elements, support nodes, loading nodes, and
   CMOD measurement nodes. `precompute_T3` forms each element's strain matrix,
   area, and shape-function gradients; `sparse_indices` caches matrix indices.
2. At a prescribed displacement, `assemble_K` scales elastic element matrices
   by `(1 - omega)` and accumulates the global sparse secant stiffness.
3. `factor_free_stiffness` factors the free-DOF block once. The inner loop
   solves equilibrium for the **previous** damage state using that factorization.
4. `damage_update` evaluates strain, modified von Mises equivalent strain,
   the nondecreasing history variable `kappa`, current principal direction,
   `oliver_bandwidth_T3`, and exponential softening. The bandwidth is
   direction dependent, not a constant element size.
5. The program reassembles stiffness with updated damage, records reaction,
   CMOD, damage, Oliver width, and the free-DOF residual, and caches the matrix
   for the next increment.

The algorithm is a **sequential secant update**. Step 3 converges at old
damage. It does not prove equilibrium at the new damage from step 4. The
`post_damage_relative_residual` column quantifies the gap. Refining the
displacement increment reduces it in the preserved 1,000 vs 10,000 step
example, but a fully coupled equilibrium solve is future work. Do not use
these curves as mesh-objectivity evidence.

## Abaqus tangent and iteration scope

The current UMAT returns the degraded elastic secant matrix in `DDSDDE`.
This is an approximate tangent for evolving damage, not the consistent
derivative of the damage law. Its effect on Abaqus iterations must be kept
in mind; solver-pass and cutback counts accompany timing. The remaining
wall time alone cannot establish whether the UMAT contains an error.
UEXTERNALDB initializes the gradient table before UMAT worker threads start. Saved gradients are read-only during the analysis, supporting Abaqus SMP. Missing gradient entries terminate the job.

## Measured timing

Run headless for comparable MATLAB timing:

```powershell
$env:FRACMATH_HEADLESS='1'
$env:FRACMATH_STEPS='10000'
matlab -batch "solver_main_3pb"
```

`matlab_timing.txt` reports wall time and assembly, factorization, damage,
and solve components. `matlab_step_diagnostics.csv` reports those components,
iteration count, old-damage convergence, and post-damage residual for each
step. `FRACMATH_CASE_DIR` may point to a separate mesh folder to avoid
overwriting the preserved run.

From the repository root, run
`python softwarex/compare_solver_diagnostics.py` to parse the preserved
MATLAB timing and Abaqus `.msg` into `solver_diagnostics.json`. The Abaqus
`.msg` gives accepted increments, cutbacks, solver passes, matrix
factorizations, and individual sparse-solver elapsed times. Its remaining
wall time is **not** a measurement of UMAT time: it also includes assembly,
convergence, output, and overhead. The different increment histories prevent
a direct speed ranking.

## Controlled mesh study

[`softwarex/MESH_STUDY.md`](../softwarex/MESH_STUDY.md) documents three exact
Abaqus/MATLAB meshes with fixed supports and loading width, separate Oliver
and fixed-law MATLAB runs, smaller-increment checks, and single-CPU Abaqus
jobs. `run_mesh_study.py` runs licensed analyses sequentially;
`analyze_mesh_study.py` checks histories and regenerates the study figure.

`FRACMATH_REGULARIZATION=fixed` holds the calibration width at
`FRACMATH_FIXED_WIDTH` (default 1.25 mm). This gives one stress–strain law on
all elements, serving as a control for element-size compensation.
The regularized default remains `oliver`.

The energy history records trapezoidal external work, stored elastic energy,
positive end-of-step damage dissipation, and their balance discrepancy.
Comparison at CMOD 0.10 mm measures partial structural dissipation. It is not
complete fracture energy. Refinement checks and post-damage residuals must be
considered when interpreting the mesh comparison. Hardware timings are evaluated separately in the size/mesh study.

## Hybrid GPU and CPU threading

`FRACMATH_BACKEND=gpu_hybrid` keeps element strain operators, reference stiffness values, and shape-function gradients on the GPU. A fused `gpuArray.arrayfun` kernel computes equivalent strain, principal direction, Oliver width, and irreversible damage/history per element in double precision. One combined gather returns damage, history, width, and strain arrays. Stiffness values are gathered before CPU sparse construction; sparse factorization and equilibrium solves remain on the CPU. Timed operations include transfers and GPU synchronization; initial device setup and precomputation are excluded from the loop timer.

`FRACMATH_THREADS=8` limits supported MATLAB numerical libraries to eight computational threads; it does not create independent `parfor` simulations. Abaqus uses `ABQ_CPUS=8` in SMP mode, with UEXTERNALDB loading the shared gradient table before material calls. The secant tangent may need many iterations during localization. The two finest large-specimen meshes use the same extended iteration limits for both thread settings, retaining default convergence tolerances.

[SCALING_STUDY.md](../softwarex/SCALING_STUDY.md) specifies matched meshes, source hashes, hardware-response checks, cost scopes, and the complete size/mesh protocol.
