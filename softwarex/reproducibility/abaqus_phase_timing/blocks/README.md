# Serial UMAT block timing

One completed small/coarse CPU1 job uses 3,584 CPS3 elements, 3,772 DOFs and 2,000 increments. All 2,001 response rows and seven mesh/boundary file hashes exactly match the uninstrumented baseline. The source generator removes its timer additions and confirms that the original constitutive statements are unchanged. There are 18,579,456 UMAT calls, 3,184 solver passes, 3,105 decompositions and no cutbacks.

| UMAT block | Raw elapsed sum (s) |
|---|---:|
| Constants and state read | 1.572 |
| Equivalent strain and history | 1.657 |
| Oliver projected width | 2.373 |
| Damage update | 1.550 |
| Stress calculation | 1.552 |
| Secant matrix | 1.631 |
| State storage | 1.564 |

The sum inside block boundaries is 11.899 s. The surrounding whole-UMAT timer is 24.934 s and includes block clocks, counter updates and between-block work; it must not be equated to an uninstrumented UMAT time. Analysis wall time is 184 s and sparse-solver message times sum to 15.438 s.

The integer-8 clock has 1,000,000 counts/s. Empty pairs average 0.08 microseconds in 100,000 calibration pairs. Their projection is 1.48635648 s per block over the observed call count, or 10.40449536 s across seven blocks. This calibration is close to the measured block sum. The microsecond clock quantizes very short blocks; instrumentation also changes compiler optimization and execution. Therefore these raw sums are diagnostic measurements, not accurate uninstrumented block costs. No subtraction, speed ranking, or performance percentages are reported. The calibration does not measure all counter/loop/clock overhead. Source and output values are archived without rounding in block_timing_summary.json.

These measurements apply to the matched small/coarse benchmark, not the different primary 10,000-step MATLAB case. They do not measure built-in Abaqus assembly or provide a full Abaqus wall-time partition. They remain outside the 90 benchmark observations.

## Reproduce verification

From the repository root:

```powershell
python softwarex/time_abaqus_umat_blocks.py --analyze-only --workspace softwarex/reproducibility/abaqus_phase_timing/blocks --source-snapshot softwarex/reproducibility/abaqus_profile/source_snapshot --baseline softwarex/reproducibility/abaqus_profile/reference_baseline
```

For a new licensed serial solve, omit --analyze-only and use a new empty workspace. Do not use the shared counters with SMP. SHA256.json records the archived file bytes.
