# Mixed-mode solver correction, 21 October 2026

The material law and parameters are unchanged. The original attempts and their accepted checkpoint are preserved in their original folders.

The new continuation solver solves the free-force equilibrium equations together with one displacement-continuation constraint. The top and side boundary displacements retain their original proportional ratio. The loading amplitude is an unknown during a continuation step. At the final endpoint, the constraint switches to the original final loading amplitude, lambda = 1.

The local continuation coordinate uses the projected strain in element 8038, multiplied by its width at the restart state. This coordinate selects progress along the equilibrium path. Its fixed projection does not freeze the crack normal or width in the material model: the damage update still uses the current Oliver projection and the unchanged total-tensile-work calibration.

The analytical tangent includes the derivatives of modified von Mises equivalent strain and Oliver width. Nondecreasing strain history and damage are committed only after convergence. Every accepted state must satisfy the original relative free-force tolerance of 1e-6; an additional check is made after committing history. Trial step convergence never depends only on a small displacement correction.

## Reproduction

Run `run_continuation` in this directory in MATLAB R2024b. Run `run_continuation_refined` for the half-step comparison. These drivers build audit_state.mat locally from the supplied accepted restart and mesh when the cache is absent. `run_audit_export.m` and damage_static.m regenerate this state from the original accepted_checkpoint.mat and mesh files. The active simulation checkpoint and accepted_progress.csv are written separately in each output directory. An interrupted run restarts from that output checkpoint.

Run `verify_analytic_tangent` to repeat the material-tangent check on 1000 damaging states.

Unsuccessful local diagnostics are not part of this published selection. Both production runs completed to lambda = 1. See verification_summary.json for equilibrium, tangent, step-refinement, and energy checks. The standard continuation required 183 additional accepted states after the saved 126-state prefix; the half-step run required 384. The maximum vertical-force difference between the continuation curves is 0.191% of the force at the restart point. The half-step energy-balance mismatch is 0.182% over the resumed path. These checks do not establish experimental accuracy.

The source snapshots damage_static.m and run_audit_export.m regenerate the mesh cache. Run verify_analytic_tangent before checking the analytical derivative. Full per-step states for the energy calculation can be regenerated with the half-step driver in a fresh workspace; final states and response histories are supplied.
