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

## What remains for a larger benchmark

Generate at least two additional mesh sizes with the same geometry and
boundary conditions, verify their element/DOF counts, and run matched
single-CPU, headless MATLAB and Abaqus jobs. Record all new `.msg`, `.sta`,
step diagnostics, hardware, versions, and peak-memory measurements. Re-run
the constitutive and structural checks on each mesh. No larger-mesh result or
GPU speedup is claimed by the current repository.
