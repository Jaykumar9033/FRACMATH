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
The paper reports accepted increments, solver passes and timing scopes.

The MATLAB bending solver also uses a sequential secant update, but its
equilibrium procedure differs from Abaqus. Similar load curves do not imply
identical convergence accuracy or justify an accuracy-matched speed ranking.

## Gradient table and parallel calls

`UEXTERNALDB` loads `oliver_t3_gradN.dat` at the synchronized analysis start.
SMP material calls then read the saved table. A missing positive element
entry terminates the run; it is not an acceptable CELENT-based paper case.
Element labels must lie between 1 and 1,000,000. The table and mesh must
refer to the same labels. Use the supplied builder and archived input hashes.

## Executed checks

- The original material test checks tensile/compressive strain mapping,
  unloading/reloading and projected width, including 16
  rotated cases.
- The manuscript-facing core audit contains 712 deterministic material states and links the actual UMAT without altering it. The separate 824-state precision archive is an optional developer extension, not a separate manuscript claim.
  An independent NumPy tensor eigensolve and deviatoric norm supply reference
  values. The actual MATLAB damage functions are copied verbatim into a
  material-point caller. Multiaxial states, previous damage/history,
  zero/isotropic strain, pure shear and STRAN/DSTRAN splits are included.
- Stress, strain history, damage, width and the documented secant matrix
  pass the tolerance `2e-10 + 2e-10 * abs(reference_value)`. These are local tests,
  not a proof of a consistent tangent or universal structural convergence.
- Completed Abaqus CPU1/CPU8 studies reproduce response CSVs and iteration
  counts within the tested configurations. The separately profiled run
  exactly reproduces its paired unprofiled response and mesh hashes.

See `reproducibility/umat_audit/README.md` for replay and compilation commands.

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
