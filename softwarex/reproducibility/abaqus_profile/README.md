# Separate Abaqus software-sampling profile

This complete small/coarse CPU1 job has 3,584 T3 elements and 3,772 DOFs,
2,000 displacement intervals and the same source, mesh and boundary sets as
observation 2 of the hardware study. The 2,001 response rows are exactly equal
in the profiled and unprofiled runs. The archive retains the input deck, mesh,
source snapshot, job diagnostics, response, VTune exports and sampling warnings.

## Identified work

VTune estimates 2.033531 s of self time in `standardU.dll` (UMAT, its helpers
and external-database initialization). Four explicitly named assembly kernels
account for 3.805141 s of self estimates. This does not allocate the remaining
work to assembly or material: callees and unknown symbols are not assigned to
those phases. The user-library code is not resolved to individual functions.

The software-sampling metric is **not** a material/assembly wall-clock timer.
The sampled Standard-process total is 187.1213 s, while Abaqus reports 40 s
rounded CPU time and 208 s elapsed time for the profiled job. These metrics
have different scopes, include profiling effects and cannot be summed or
rescaled into phase wall times. Named self samples describe this profile,
not the absolute phase costs of the 90 unprofiled benchmark observations.
Missing symbols and a PulseEvent API warning further limit interpretation.
Other numerical validation jobs were active; this is not an isolated timing
observation. Sparse-solver message timers give 3,184 passes and 20.23 s in
this separate job. No profiled value enters the hardware performance table.

## Inspect and reproduce

From the repository root, regenerate the inspection summary:

```powershell
python softwarex/analyze_abaqus_profile.py --workspace softwarex/reproducibility/abaqus_profile --baseline softwarex/reproducibility/abaqus_profile/reference_baseline
```

For a new collection, with licensed Abaqus/Fortran and Intel VTune installed:

```powershell
python softwarex/profile_abaqus.py --workspace C:/runs/abaqus_profile --source-snapshot softwarex/reproducibility/abaqus_profile/source_snapshot
```

The launcher sets a native Windows PowerShell module path only for its own
process tree and stops collection after successful analysis, so compiler
telemetry cannot keep the collector open indefinitely. It reuses complete
existing reports and preserves failed attempts. Raw VTune databases and
proprietary application binaries are retained locally, not in this archive;
the full exported function and call-stack data support inspection.
