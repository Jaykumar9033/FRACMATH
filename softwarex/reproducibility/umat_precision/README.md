# UMAT batch timing and material-point verification

The production UMAT is linked unchanged with an external Fortran driver. Five observations each make 14,240,000 calls using 712 deterministic material inputs, repeated 20,000 times. There are four state variables to verify the projected width and table flag. One untimed pass initializes the table and warms the code. Actual and empty-driver observation order alternates. Only one Windows QueryPerformanceCounter pair surrounds each complete batch; there are no clocks inside the production UMAT.

| Measurement | Median (s) | Range (s) |
|---|---:|---:|
| Actual UMAT plus driver | 1.144683 | 1.128599–1.240728 |
| Empty call plus driver | 0.126594 | 0.123496–0.129791 |

Actual batch elapsed-time coefficient of variation is 3.96%. Clock frequency is 10,000,000 Hz, observed minimum positive interval is 0.1 microseconds, and the 100,000-pair calibration mean is 0.015148 microseconds. Batch timings include driver resets, calls and output checksums. Empty-driver time is reported separately without subtraction; it is not an exact correction. The independent reference verifies the actual and control checksums. The calibration is recorded in batch/clock_calibration.csv.

These are standalone cached material-point measurements with Intel ifx /O2. They are not Abaqus assembly or full-job times, do not represent the structural distribution of material states, and cannot be extrapolated to the job's UMAT cost. They improve the measurement interval compared with intrusive per-call clocks without claiming precise costs for individual UMAT blocks. The previous seven-block in-job diagnostics remain available with their clock-overhead limitation.

## Material verification

824 cases pass the actual UMAT versus independent tensor-eigensolve reference and actual MATLAB damage-function comparison with absolute plus relative tolerance 2e-10. They comprise the original 712 cases and 112 states across 16 tension, shear, compression and rotating-strain paths at four projected widths. Prior states in path inputs come from the independent reference. History and damage are nondecreasing; all returned secant matrices are symmetric positive semidefinite. This checks the documented secant matrix, not a consistent damage tangent or universal structural convergence. The maximum differences are recorded in history/summary.json.

## Replay

From the repository root:

```powershell
python softwarex/run_umat_precision.py --workspace softwarex/reproducibility/umat_precision --analyze-only
```

For fresh executable measurements use a new workspace and omit --analyze-only. The runner needs Windows, Intel ifx 2025.0 and MATLAB R2024b by default; --matlab can specify the MATLAB executable. --prepare-only writes sources without running them. The compiler command files show flags, linking and utility stubs. Source snapshots, inputs, outputs and raw timings are included; generated executable/object files are not distributed. SHA256.json identifies their bytes.

Timer API: [Microsoft QueryPerformanceCounter documentation](https://learn.microsoft.com/en-us/windows/win32/api/profileapi/nf-profileapi-queryperformancecounter).

## Fresh-process replay

The complete runner also succeeds in a second fresh process, including Fortran compilation, MATLAB execution and all 824 reference comparisons. Its actual-batch coefficient of variation is 0.81%. Both processes together provide ten actual batches (142.4 million calls), median 1.148423 s and range 1.128599–1.240728 s. Combined empty-driver median is 0.128149 s. All observations are retained; the first process's slower batch is not discarded. `fresh_replay/` contains its full reproduction sources and outputs.
