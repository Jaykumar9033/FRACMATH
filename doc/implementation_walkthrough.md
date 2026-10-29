# Implementation walkthrough

The executable bending implementation is `3pb/matlab/solver_main_3pb.m`. Its
`softwarex/reproducibility/2d/` copy is kept identical for the submission
package. This is a documented implementation of established continuum damage
and Oliver crack-band regularization, not a new constitutive law.

## Start with the supplied example

From the repository root, open `softwarex/start_here.m` in MATLAB and press
**Run**, or use:

```powershell
matlab -batch "run('softwarex/start_here.m')"
```

The entry script selects the supplied medium mesh, 2,000 fixed increments,
-0.1 mm final prescribed displacement, one CPU thread, Oliver width and
modified von Mises equivalent strain. It sets the solver controls explicitly
and writes to `softwarex/student_results`, keeping the archived results
available. Set `show_figures = false` in the entry script when measuring time.
The completed medium/fine MATLAB-Abaqus pairs use the same exact mesh within
each pair and these same increment and displacement settings.

## Load-step algorithm

1. `load_mesh` reads nodes, T3 elements, support nodes, loading nodes and
   CMOD measurement nodes. `precompute_T3` forms each element's strain matrix,
   area and shape-function gradients; `sparse_indices` caches matrix indices.
2. At a prescribed displacement, `assemble_K` scales elastic element matrices
   by `(1 - omega)` and accumulates the global sparse secant stiffness.
3. `factor_free_stiffness` factors the free-DOF block once. The inner loop
   solves equilibrium for the **previous** damage state using that factorization.
4. `damage_update` evaluates strain, the selected equivalent strain,
   the nondecreasing history variable `kappa`, the selected crack-band width
   and exponential softening. The default uses modified von Mises strain
   and the direction-dependent `oliver_bandwidth_T3` calculation.
5. The program reassembles stiffness with updated damage, records reaction,
   CMOD, damage, crack-band width and the free-DOF residual, and caches the
   matrix for the next increment.

The algorithm is a **sequential secant update**. Step 3 converges at old
damage. It does not prove equilibrium at the new damage from step 4. The
`post_damage_relative_residual` column quantifies the gap. A complete MATLAB
history therefore does not imply that each updated state satisfies Abaqus's
equilibrium criterion. Matching the increment count does not make the
nonlinear algorithms identical. Curve agreement and mesh sensitivity should
be interpreted together with these residuals.

## Abaqus tangent and iteration scope

The current UMAT returns the degraded elastic secant matrix in `DDSDDE`.
This is an approximate tangent for evolving damage, not the consistent
derivative of the damage law. Its effect on Abaqus iterations must be kept
in mind; solver-pass, factorization and accepted-increment counts accompany
timing. The remaining wall time alone cannot establish whether the UMAT
contains an error.

UEXTERNALDB initializes the gradient table before UMAT worker threads start.
Saved gradients are read-only during the analysis, supporting Abaqus SMP.
Missing gradient entries terminate the job.

## Measured timing

`matlab_timing.txt` reports wall time and assembly, factorization, damage
and backsolve components. `matlab_step_diagnostics.csv` reports those
components, iteration count, old-damage convergence and post-damage residual
for each step. `FRACMATH_CASE_DIR` may point to a separate mesh folder to
avoid overwriting a preserved run.

The current medium and fine fixed-increment comparisons each have one
timing observation per program. MATLAB's saved reference load-loop times
are 337.30 and 967.09 s; the separate Abaqus analysis/output times are
2,843 and 4,538 s. MATLAB factorization plus backsolve takes 263.66 and
789.38 s. Abaqus's summed reported solver elapsed times are 296.54 and
593.40 s. These are different measured scopes and different sequences of
equilibrium operations, so they do not establish an inherent solver-speed
ranking or a repeated-run speedup.

The Abaqus `.msg` gives accepted increments, solver passes, matrix
factorizations and individual sparse-solver elapsed times. Its remaining
wall time is **not** a measurement of UMAT time: it also includes assembly,
convergence, output and overhead. The separate material-call and native
profiling diagnostics do not allocate this entire remainder for the current
medium/fine jobs. Input/source hashes, actual fixed schedules, histories,
timing files and analysis checks are in
`softwarex/reproducibility/fixed_increment_extension/`.

## Controlled mesh and formulation comparisons

The current CPU study compares `FRACMATH_REGULARIZATION=area`, which uses
`h = sqrt(2*A)` for each triangle of area `A`, with
`FRACMATH_REGULARIZATION=oliver`. Oliver width projects the shape-function
gradients onto the current maximum-principal-strain direction. Area width
follows element size but does not depend on strain direction. Coarse,
medium and fine pairs retain their exact mesh, material parameters and
2,000-increment displacement schedule.

The current coarse-mesh CPU comparison uses two damage drivers: modified von Mises and Rankine stress. Figure 4 shows load versus CMOD. All use the same mesh, 2,000 fixed increments, Oliver width formula, tensile onset and exponential energy calibration. These are scalar-driver alternatives within the same damage update, not complete independently calibrated concrete models. Only modified von Mises uses fc/ft. See [EQUIVALENT_STRAIN_STUDY.md](../softwarex/EQUIVALENT_STRAIN_STUDY.md) for formulas, checks and reproduction commands.

[COMPARISON_EXTENSION.md](../softwarex/COMPARISON_EXTENSION.md) explains the
current execution and failure policy. Original failed fixed Abaqus cases
are preserved. The coarse 4,000-increment pair passes actual schedule,
complete loading-coverage and finite-output checks. The baseline 20,000-step
attempt fails, with 5,174 converged increments verified from its ODB history.
No adaptive history replaces a failed fixed-increment comparison.

Optional developer energy histories record trapezoidal external work,
stored elastic energy, positive end-of-step damage dissipation and their
balance discrepancy. These energy quantities are not current manuscript
results. An optional archived comparison at CMOD 0.10 mm measures partial
structural dissipation, not complete fracture energy. Post-damage residuals
must be considered when interpreting the current mesh comparison.

## Hybrid GPU and CPU threading

`FRACMATH_BACKEND=gpu_hybrid` keeps element strain operators, reference
stiffness values and shape-function gradients on the GPU. A fused
`gpuArray.arrayfun` kernel computes modified von Mises equivalent strain,
principal direction, Oliver width and irreversible damage/history per
element in double precision. One combined gather returns damage, history,
width and strain arrays. Stiffness values are gathered before CPU sparse
construction; sparse factorization and equilibrium solves remain on the
CPU. Timed operations include transfers and GPU synchronization; initial
device setup and precomputation are excluded from the loop timer.

The current hybrid kernel supports the Oliver/modified-von-Mises path.
Its retained constant-width branch serves older archive reproduction.
The area-width and alternative equivalent-strain comparisons use CPU execution; selecting
these options with the hybrid backend raises an explicit error. Their CPU results
do not establish GPU performance or CPU/GPU agreement for those options.

`FRACMATH_THREADS=8` limits supported MATLAB numerical libraries to eight
computational threads; it does not create independent `parfor` simulations.
Abaqus uses `ABQ_CPUS=8` in SMP mode, with UEXTERNALDB loading the shared
gradient table before material calls. The secant tangent may need many
iterations during localization. The current matched medium/fine comparisons
use one computational thread in each program.

[SCALING_STUDY.md](../softwarex/SCALING_STUDY.md) specifies the optional
archived size/mesh/hardware protocol with its own source hashes, response
checks and timing scopes. Older baseline, constant-width and
adaptive-increment records remain archive evidence; they are not the current
manuscript comparison suite. [MESH_STUDY.md](../softwarex/MESH_STUDY.md) and
`compare_solver_diagnostics.py` replay those earlier records.

## Softening calibration in the 3D examples

The bending and torsion solvers use the paper formula `epsilon_f = kappa_0/2 + G_F/(h*f_t)` and the
exponential denominator `epsilon_f - kappa_0`. This calibration includes the
elastic contribution in the specified uniaxial work. The panel solver uses
`beta = ft*h/GF` with
`omega = 1 - (kappa0/kappa)*exp(-beta*(kappa-kappa0))` above onset, calibrating
the post-onset tail. These are separately stated energy conventions; their
parameter values must not be interchanged when reproducing the examples.
The qualitative mixed-mode illustration and the pure-tension mesh study
are distinct panel cases, with Nooru-Mohamed retained as the benchmark source.

## Shared notation

See [Symbols and code names](../softwarex/NOTATION.md) for the common definitions used in the paper, flowchart, MATLAB and UMAT.
