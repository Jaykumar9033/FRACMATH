# Abaqus timing scopes

The completed three-mesh jobs provide elapsed wall time, sparse-solver elapsed time, rounded analysis CPU totals, accepted increments, cutbacks, solver passes, and decompositions. The final `.dat` CPU totals are 531, 1100, and 2550 seconds for coarse, medium, and fine cases.

The `.msg` and `.dat` records do not expose separate UMAT and global stiffness-assembly timers. The unallocated elapsed remainder is not a material or assembly measurement.

A standalone per-call timing probe with one million elastic UMAT calls measured 0.035–0.036 seconds without instrumentation and 0.195–0.198 seconds with instrumentation. The one-microsecond clock resolution and timer overhead dominate these short calls. Those timings are rejected as material-time estimates.

Windows Performance Recorder CPU profiling was attempted in the available session. It returned error `0xc5585011`: profiling privileges could not be enabled. An administrator-enabled profiling session or a vendor phase report is required to attribute proprietary assembly routines. No material/assembly split is inferred from the remaining elapsed time.
