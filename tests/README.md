# Package smoke checks

These checks read current medium-mesh inputs and matched MATLAB/Abaqus histories. They check connectivity, complete finite histories, reference peaks and the presence of current 3D verification and timing records. They do not run structural simulations.

From the repository root in MATLAB:

```matlab
addpath('tests')
run_smoke_checks
```

Expected output: `FRACMATH smoke checks passed.`

Use [REPRODUCIBILITY.md](../REPRODUCIBILITY.md) for numerical verification and figure reconstruction.
