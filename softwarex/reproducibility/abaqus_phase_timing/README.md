# Abaqus UMAT timing and native assembly profile

Two separate single-CPU, small/coarse runs use the same 3,584 CPS3 elements and 3,772 DOFs as the matched benchmark. Both finish 2,000 increments. Their 2,001 response rows are exactly equal to the archived unprofiled baseline, and all seven mesh/boundary hashes match. These diagnostic runs are outside the 90 benchmark observations.

## Direct UMAT measurement

`direct/direct_timing_summary.json` records 18,579,456 calls and a raw elapsed-call sum of 2.996 s. INTEGER(8) SYSTEM_CLOCK reads bracket the actual unchanged constitutive calculations. The clock rate is 1,000,000 counts/s. Empty clock pairs average 0.09 microseconds in a separate 100,000-pair calibration; multiplying by the call count gives 1.67215104 s. This projection is a diagnostic, not an exact overhead correction, and is not subtracted. The timer adds overhead to the complete solve. Raw call sums include clock effects and possible scheduling; they are not an uninstrumented material phase wall time.

The job completes 2,000 accepted increments, 3,184 solver passes, 3,105 decompositions and no cutbacks. Its sparse-solver message timers sum to 15.33 s; reported analysis wall time is 162 s. These timing scopes are not added into a complete phase allocation. Counters are serial only; do not use this instrumentation for SMP. The permanent job log contains the raw FRAC_TIMER records.

## Native-only profile

`native_profile/analysis_summary.json` records 1.917316 s of sampled user-library self time and 2.873473 s in four named assembly routines. Collection and all three exports return zero. VTune attaches only to standard.exe after startup; early initialization is outside its window. The user PDB is preserved locally, but the temporary DLL is removed before final symbol resolution, leaving user-library samples unresolved to individual routines. Vendor/system symbols are also incomplete and PulseEvent warnings are retained. The profiler totals 139.314 s of sampled CPU-time estimates while Abaqus reports 24 s rounded CPU and 161 s wall time. Their scopes differ; no sum or rescaling is used. No complete assembly wall timer is available. Sampled CPU self times exclude callees and unidentified work. They must not be combined with the direct elapsed-call measurement.

## Reproduce the checks

From the repository root:

```powershell
python softwarex/time_abaqus_umat.py --analyze-only --workspace softwarex/reproducibility/abaqus_phase_timing/direct --source-snapshot softwarex/reproducibility/abaqus_profile/source_snapshot --baseline softwarex/reproducibility/abaqus_profile/reference_baseline
python softwarex/analyze_abaqus_profile.py --workspace softwarex/reproducibility/abaqus_phase_timing/native_profile --baseline softwarex/reproducibility/abaqus_profile/reference_baseline
```

For licensed fresh runs use time_abaqus_umat.py or profile_native_abaqus.py with a new --workspace and the same --source-snapshot. The direct-timer command also needs --baseline. Run them sequentially. VTune is required only for native profiling. SHA256.json files identify the archived raw sources and outputs. Local proprietary executables, raw VTune databases and PDB files are not part of the repository; the full CSV exports and warnings are provided.

## UMAT block measurements

The [seven-block diagnostic](blocks/README.md) records constants/state, strain/history, Oliver width, damage, stress, secant matrix and state storage. Response and mesh checks pass. Clock calibration is large relative to these short blocks, so the archive reports raw sums without claiming precise uninstrumented percentages.
