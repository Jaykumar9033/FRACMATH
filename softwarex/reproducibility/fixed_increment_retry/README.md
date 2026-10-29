# Matched smaller fixed-increment comparison

The coarse case completes 4,000 fixed increments in both MATLAB and Abaqus on
the same exact mesh, to -0.1 mm. Both saved histories are finite and their
actual displacement/time schedules pass the stated storage tolerances.
MATLAB peak: 4,156.569 N; Abaqus peak: 4,116.424 N. The MATLAB peak is 0.9752%
higher relative to Abaqus; common-CMOD RMS is 0.8511% of the MATLAB peak.

MATLAB load-loop time is 410.99 s, including 79.02 s assembly, 282.70 s
factorization, 37.25 s backsolve, 10.19 s damage and 1.83 s other work.
Abaqus analysis/output wall time is 1,278 s. Its message-file solver sum is
113.85 s over 6,140 passes, with 1,164.15 s unallocated remainder. These are
one-observation measurements with distinct algorithms/scopes, not an inherent
speed ranking. The remainder cannot be labelled complete assembly time.
Two alternate-force-tolerance acceptance messages occur in the completed
Abaqus record. No NO STOP override or adaptive replacement is used.

The exact-mesh baseline reference completes 20,000 MATLAB increments to -0.2 mm.
The Abaqus attempt fails during increment 5,175; the ODB confirms 5,174
converged increments, ending at -0.051739998 mm. Message-file TOTAL OF 5,175
includes the failed attempt and must not be called an accepted count.
Only its converged history is plotted as a separate failure diagnostic.
The failure message reports divergence and FIXED TIME INCREMENT IS TOO LARGE.
Its incomplete Abaqus timing is not compared with a full MATLAB timing as
a speed result. A secant material matrix can hinder convergence; this record
alone does not identify a unique numerical cause or establish a material bug.

Recheck without numerical analysis:

```powershell
python softwarex/verify_fixed_retry.py --workspace softwarex/reproducibility/fixed_increment_retry --output C:/runs/retry_check
```

Source snapshots, exact meshes, MATLAB states, actual ODB history exports,
message/status files, execution records and verification summary are supplied.
ODB files, host environment dumps and compiled scratch files are omitted.
