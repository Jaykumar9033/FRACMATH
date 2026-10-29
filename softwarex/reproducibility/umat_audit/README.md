# Actual UMAT material-point audit

712 deterministic cases pass the independent reference and actual MATLAB
damage-function comparisons. `summary.json` records tolerances and maximum
differences. The archived UMAT is the exact source linked in the executable.
No numerical UMAT change was made for these checks.

Replay the numerical comparisons from the repository root:

```powershell
python softwarex/audit_umat.py --workspace softwarex/reproducibility/umat_audit --check
```

For a fresh executable test, prepare a separate workspace:

```powershell
python softwarex/audit_umat.py --workspace C:/runs/umat_audit
```

In an Intel Fortran command prompt, change to that workspace and compile:

```text
ifx /O2 /extend-source /names:lowercase /include:"C:/SIMULIA/EstProducts/2024/SMAUsubs/PublicInterfaces" C:/path/FRACMATH/3pb/abaqus/cdm_umat_2d_OLIVER_T3_FAST.for C:/path/FRACMATH/softwarex/umat_point_audit.f90 /exe:umat_point_audit.exe
umat_point_audit.exe
matlab -batch run_matlab_points
```

Then execute the comparison with `--check` and the fresh workspace path.
The tested environment is MATLAB R2024b and Intel ifx 2025.0.4 on Windows.
The wrapper contains the original MATLAB local damage functions verbatim;
`source.json` identifies their tested source hash. GETOUTDIR and XIT stubs
replace Abaqus utility calls only in this standalone executable.

The check verifies the supplied degraded elastic secant matrix. It does not
claim that this matrix is the consistent derivative of an evolving damage
law. See `../../UMAT_GUIDE.md` for implementation and convergence limits.
