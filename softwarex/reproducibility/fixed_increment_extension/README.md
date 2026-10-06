# Fixed-increment bending and material-formulation evidence

This archive supplies the numerical data for the current SoftwareX bending,
area-width and equivalent-strain figures. No simulations are started by the
figure-reconstruction scripts.

## Completed results

- Medium and fine MATLAB/Abaqus comparisons use the same mesh, 2,000 prescribed
  increments and final displacement of -0.1 mm. Actual Abaqus history times and
  displacements are saved in `abaqus_schedule.csv` and checked independently.
- CPU MATLAB area-width cases use h = sqrt(2*A_e) on three controlled meshes.
- The coarse CPU case compares modified von Mises with maximum positive
  principal strain, using Oliver width in both runs.
- Source snapshots, mesh hashes, state files, curves, execution records and
  Abaqus message/status files are included. ODB files and compiled scratch
  files are omitted; the supplied inputs and extraction script recreate exports.

## Preserved diagnostics

The original 10,000-increment baseline and 2,000-increment coarse Abaqus runs
did not converge through the requested loading interval. Their partial histories
are diagnostic records, not completed response curves. No adaptive replacement
or NO STOP acceptance was used. The old baseline MATLAB reference also has
coordinate rounding up to 5.4993e-7 mm; its exact-mesh check correctly fails.
The aggregate execution summary therefore remains `completed_needs_review`.

The fresh exact-mesh baseline 20,000-increment retry also failed. Its finished
attempt is preserved in the separate `fixed_increment_retry` archive. The coarse
4,000-increment retry remains running. Neither is evidence for the current plots.

## Timing scope

Saved MATLAB times measure the load loop. Abaqus times measure analysis and
output. Solver entries are extracted from Abaqus `.msg` files. The remainder
includes material work, assembly, convergence, output and overhead; it is not
a separately measured assembly time. These are one-observation diagnostics
and do not establish an inherent solver-speed or overall program ranking.

The default numerical formulation is Oliver width and modified von Mises
strain. The new area/maximum-principal options are verified for CPU execution.
The hybrid GPU uses the previous default kernel and CPU sparse factorization.

See `../../COMPARISON_EXTENSION.md` for execution and verification commands.
`SHA256SUMS.txt` records the exact bytes in this archived evidence package.
