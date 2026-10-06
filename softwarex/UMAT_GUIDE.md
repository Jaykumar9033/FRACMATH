# Reading and checking the UMAT

The UMAT is for small-strain, isothermal CPS3 plane-stress elements. Read
`3pb/abaqus/cdm_umat_2d_OLIVER_T3_FAST.for` in this order:

1. Read `E`, `nu`, `ft`, `GF` and the compression/tension ratio from `PROPS`.
2. Add `STRAN` and `DSTRAN` to get the trial total strain. The third entry
   is engineering shear, so the tensor shear entry is half that value.
3. Calculate principal strains and the equivalent strain.
4. Read the element gradients and project them onto the principal direction
   to calculate the crack-band width.
5. Take the larger of the previous and trial equivalent strains. Calculate
   damage and prevent it from falling below its previous value.
6. Multiply the elastic stress and stiffness by `1 - damage`.
7. Return trial `STATEV(1)` (strain history) and `STATEV(2)` (damage).
   With four state variables, entries 3 and 4 store width and the table flag.

## What the tangent means

`DDSDDE` contains degraded elastic stiffness. It is a **secant matrix**,
not the full derivative of stress when damage and direction change.
Abaqus can need additional equilibrium iterations and cutbacks during
softening. A slow run alone does not establish a material-law bug.
The current paper uses completed medium/fine fixed-increment comparisons and explicitly scoped timing records. The original failed fixed jobs are retained separately.

The MATLAB bending solver also uses a sequential secant update, but its
equilibrium procedure differs from Abaqus. Similar load curves do not imply
identical convergence accuracy or justify an accuracy-matched speed ranking.

## Gradient table and parallel calls

`UEXTERNALDB` loads `oliver_t3_gradN.dat` at the synchronized analysis start.
SMP material calls then read the saved table. A missing positive element
entry terminates the run; it is not an acceptable CELENT-based paper case.
Element labels must lie between 1 and 1,000,000. The table and mesh must
refer to the same labels. Use the supplied builder and archived input hashes.

## Correctness checks and fixed-increment status

- The original material test checks tensile/compressive strain mapping,
  unloading/reloading and projected width, including 16
  rotated cases.
- The manuscript uses ten explained material states and links the actual UMAT without altering it. The larger audits are optional developer records.
  An independent NumPy tensor eigensolve and deviatoric norm supply reference
  values. The actual MATLAB damage functions are copied verbatim into a
  material-point caller. Multiaxial states, previous damage/history,
  zero/isotropic strain, pure shear and STRAN/DSTRAN splits are included.
- Stress, strain history, damage, width and the documented secant matrix
  pass the tolerance `2e-10 + 2e-10 * abs(reference_value)`. These are local tests,
  not a proof of a consistent tangent or universal structural convergence.
- The completed medium/fine structural comparisons use the same exact paired meshes, 2,000 fixed increments and -0.1 mm final displacement. Actual ODB history times and loading displacement are checked. Matching the increment schedule does not make MATLAB and Abaqus equilibrium accuracy identical.
- Original baseline 10,000-increment and coarse 2,000-increment fixed Abaqus runs stopped during convergence. Their converged histories and logs are preserved. The baseline 20,000-increment retry also failed after 5,175 accepted increments recorded in `.sta`; its diagnostic logs and exact MATLAB reference are in `reproducibility/fixed_increment_retry/baseline/`. The coarse 4,000-increment retry is running and requires final verification before use as a complete paired curve. There is no adaptive substitution or NO STOP acceptance override.
- Earlier CPU1/CPU8 adaptive-increment studies and their solution counts remain optional archive records. The separately profiled diagnostic reproduces its paired unprofiled response and mesh hashes; it is not the current fixed-increment timing observation.

See `reproducibility/material_examples/README.md` for inputs, replay and compilation commands.

## Efficiency review

Inspection of the actual Fortran source identifies these existing choices:

- The gradient table is loaded once through `UEXTERNALDB` before worker material calls. Normal material calls read the saved arrays rather than reopening the file.
- Element labels directly index the six gradient arrays. There is no per-call search through the full table.
- Stress and secant-stiffness entries are written explicitly for the small plane-stress matrix, avoiding a general small matrix multiplication.
- Two state variables hold the required history and damage. Optional width/table flags add diagnostic output when four state variables are requested.

These are implementation choices, not proof that the routine is optimal. Separate material-call and batch timings retain clock/driver overhead and their own scopes; they do not identify complete Abaqus material or assembly time. A possible future improvement is to reuse material constants or principal-direction calculations. Such changes have not been benchmarked or adopted, and would require constitutive equivalence, SMP safety and end-to-end timing checks.

The returned matrix remains secant. A consistent tangent is a separate numerical development requiring its own derivative and convergence verification. The current fixed-increment failures do not by themselves establish a UMAT coding error, and material-point agreement does not guarantee structural convergence for every loading schedule.

## Limits

This routine is not a general 3D, finite-strain, thermal or cyclic concrete
model. It does not populate the optional Abaqus energy bookkeeping outputs;
energy fields in the optional developer archives are not manuscript results. Material constants and bandwidth must
permit the chosen softening calibration. A secant tangent and the declared
constitutive assumptions must be considered when interpreting results.

# Code style

The beginner entry uses plain settings and four numbered steps. Numerical
functions retain meaningful variables, ordinary control flow and comments
explaining physical quantities. Vectorized element operations and sparse
factorization require concepts beyond introductory MATLAB. The beginner
guide explains their array dimensions; rewriting them as a different solver
would require new numerical verification. Start with the CPU example and
use the array-size table while reading the element operations.

## Batch timing and history checks

The optional [material-point precision archive](reproducibility/umat_precision/README.md) contains additional states and timing batches for developer auditing. It is not needed for the manuscript verification path, and its batch elapsed time is not an Abaqus job-phase measurement.
