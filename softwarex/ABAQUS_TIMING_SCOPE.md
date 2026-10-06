# Abaqus timing measurement scope

The manuscript timing table uses completed coarse, medium and fine fixed-increment comparisons. Medium/fine records are in `reproducibility/fixed_increment_extension/timing_breakdown_current.json`; the coarse record is in `reproducibility/fixed_increment_retry/final_verification/summary.json`. Both programs use the exact same mesh and schedule within each pair, with -0.1 mm final displacement. The coarse pair uses 4,000 increments; medium/fine use 2,000.

MATLAB source is available, so elapsed timers surround assembly, factorization, damage updates and free-block solves. The Abaqus UMAT source is available, but the built-in element assembly, factorization, convergence checks and output routines are not exposed as source-level timer boundaries in this installation. No supported setting for a complete equivalent phase breakdown was identified in the installed site settings or the official output documentation checked.

| Quantity | Available evidence | Interpretation |
|---|---|---|
| Analysis wall time | Completed job time summary | Total for the analysis scope |
| Sparse-solver elapsed time | Sum of per-pass message-file timers | Solver scope reported by Abaqus; not a separate factorization/backsolve partition |
| Actual UMAT calls | Instrumented serial rerun | Raw elapsed-call sum includes clock effects; not all element/material work |
| Assembly routines | Native-only VTune rerun | Identified CPU self samples only; excludes callees and unidentified work |
| Remaining wall time | Total minus reported solver elapsed | Unallocated; cannot be labelled assembly or material time |

## Current fixed-increment observations

All values below are seconds.

| Component | MATLAB medium | MATLAB fine | Abaqus medium | Abaqus fine |
| --- | ---: | ---: | ---: | ---: |
| Assembly | 63.38 | 153.19 | Not separately measured | Not separately measured |
| Factorization | 227.54 | 681.30 | Included in reported solver time | Included in reported solver time |
| Backsolve | 36.12 | 108.08 | Included in reported solver time | Included in reported solver time |
| Damage/material | 8.97 | 21.26 | Not separately measured | Not separately measured |
| Combined solver | 263.66 | 789.38 | 296.54 | 593.40 |
| Other/unallocated remainder | 1.29 | 3.26 | 2546.46 | 3944.60 |
| Total recorded scope | 337.30 | 967.09 | 2843.00 | 4538.00 |

MATLAB combined solver time is factorization plus backsolve; do not add that row again when summing the components. Abaqus solver time is the sum of 6,225 medium and 7,566 fine `.msg` timer entries. It is not a separate factorization/backsolve measurement.

These are single observations. MATLAB times are saved reference load-loop measurements; Abaqus times are from separate fresh fixed-increment analyses and include analysis/output. The nonlinear algorithms, solver-call counts and timing scopes differ. The lower accumulated Abaqus solver time for the fine case does not establish an inherent ranking of the linear solvers. The unallocated Abaqus remainder includes several types of work and cannot be labelled assembly alone.

The completed coarse 4,000-increment pair records MATLAB 410.99 s load-loop time, including 79.02 s assembly, 282.70 s factorization, 37.25 s backsolve, 10.19 s damage and 1.83 s other work. Its combined MATLAB solver time is 319.95 s. Abaqus records 1,278 s analysis/output wall time, 113.85 s summed solver time over 6,140 passes and 1,164.15 s unallocated remainder. Two alternate-force-tolerance acceptance messages are retained in its log; this does not establish identical equilibrium accuracy between programs.

The original baseline/coarse fixed jobs and the baseline 20,000-increment retry failed. The retry ODB confirms 5,174 converged increments; reported attempt 5,175 failed. These incomplete runs are diagnostics and are excluded from completed timing comparisons. Their records remain under `reproducibility/fixed_increment_retry/baseline/`.

## Optional earlier diagnostics

The earlier adaptive-increment baseline reports 832 s wall time, 100.15 s summed sparse-solver time and a 731.85 s remainder. These values remain an archival observation; they are not the current manuscript timing-table values.

Optional developer diagnostic commands, source snapshots, response comparisons and logs are in [the measurement archive](reproducibility/abaqus_phase_timing/README.md). These archived diagnostics are separate from the manuscript timing table and are not used to allocate its assembly or material times. A subsequent [seven-block UMAT rerun](reproducibility/abaqus_phase_timing/blocks/README.md) measures the available source blocks. Its response checks pass, but clock effects prevent precise uninstrumented block percentages. It does not reveal the unavailable built-in assembly boundaries.

A complete phase allocation would require a vendor-supported detailed performance report or sufficiently complete instrumentation of the internal routines. A more detailed sampling profile can improve attribution, but it remains an estimate rather than the directly measured MATLAB elapsed breakdown. Replacing built-in elements with a user element would change the implementation being benchmarked and would not measure the current built-in assembly path.

Official documentation consulted: [Abaqus Output Guide](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEOUTRefMap/simaout-c-ov.htm), [Generating diagnostic information](https://docs.software.vt.edu/abaqusv2025/English/SIMACAECAERefMap/simacae-c-outgenerate.htm), and [User subroutines and utilities](https://docs.software.vt.edu/abaqusv2025/English/SIMACAESUBRefMap/simasub-c-subroutineover.htm). These describe output and user-subroutine interfaces; they do not establish that the unavailable full timing partition has been measured.

## External batch timing

The [standalone batch benchmark](reproducibility/umat_precision/README.md) places high-resolution timers outside 14.24-million-call batches of the unchanged UMAT. This avoids per-call clock intrusion but includes driver work and cached synthetic inputs. It is distinct from in-job Abaqus timings and does not isolate assembly or exact block percentages.
