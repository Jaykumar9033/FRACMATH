# Abaqus timing measurement scope

Checked against the installed Abaqus 2024 environment and the completed job logs on 4 October 2026.

MATLAB source is available, so elapsed timers surround assembly, factorization, damage updates and free-block solves. The Abaqus UMAT source is available, but the built-in element assembly, factorization, convergence checks and output routines are not exposed as source-level timer boundaries in this installation. No supported setting for a complete equivalent phase breakdown was identified in the installed site settings or the official output documentation checked.

| Quantity | Available evidence | Interpretation |
|---|---|---|
| Analysis wall time | Completed job time summary | Total for the analysis scope |
| Sparse-solver elapsed time | Sum of per-pass message-file timers | Solver scope reported by Abaqus; not a separate factorization/backsolve partition |
| Actual UMAT calls | Instrumented serial rerun | Raw elapsed-call sum includes clock effects; not all element/material work |
| Assembly routines | Native-only VTune rerun | Identified CPU self samples only; excludes callees and unidentified work |
| Remaining wall time | Total minus reported solver elapsed | Unallocated; cannot be labelled assembly or material time |

The main completed Abaqus case reports 832 s wall time and 100.15 s summed sparse-solver elapsed time. Its remainder is 731.85 s. These are the values in the manuscript's Abaqus timing table.

The separate small/coarse diagnostic run reports 2.996 s across 18,579,456 actual UMAT calls, with an empty-clock-pair projection of 1.672 s. The projection is not an exact overhead correction and is not subtracted. The separate native profile estimates 2.873 s of self CPU work in four identified assembly routines. These diagnostic quantities do not form an additive partition of the main run or of each other.

Completed diagnostic commands, source snapshots, response comparisons and logs are in [the measurement archive](reproducibility/abaqus_phase_timing/README.md). Both completed diagnostics reproduce their baseline response and mesh/boundary hashes exactly. No additional numerical rerun was performed for this feasibility check: repeating those collectors would not reveal unsupported internal timer boundaries.

A complete phase allocation would require a vendor-supported detailed performance report or sufficiently complete instrumentation of the internal routines. A more detailed sampling profile can improve attribution, but it remains an estimate rather than the directly measured MATLAB elapsed breakdown. Replacing built-in elements with a user element would change the implementation being benchmarked and would not measure the current built-in assembly path.

Official documentation consulted: [Abaqus Output Guide](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEOUTRefMap/simaout-c-ov.htm), [Generating diagnostic information](https://docs.software.vt.edu/abaqusv2025/English/SIMACAECAERefMap/simacae-c-outgenerate.htm), and [User subroutines and utilities](https://docs.software.vt.edu/abaqusv2025/English/SIMACAESUBRefMap/simasub-c-subroutineover.htm). These describe output and user-subroutine interfaces; they do not establish that the unavailable full timing partition has been measured.
