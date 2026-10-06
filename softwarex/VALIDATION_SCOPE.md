# Validation and verification scope

FRACMATH implements established continuum-damage and crack-band methods. The article checks the software implementation and numerical behavior; it does not introduce a new constitutive theory.

## What is checked

- **Material point:** ten prescribed states compare MATLAB, the actual Abaqus UMAT and independent reference calculations. The permitted difference is `2e-10 + 2e-10 * abs(reference_value)`. These are not one-element structural analyses.
- **Matched fixed increments:** completed medium/fine bending cases use identical meshes, 2,000 fixed increments and -0.1 mm final displacement in MATLAB and Abaqus. Actual ODB times and loading displacement are checked; load-CMOD curves provide structural response comparisons.
- **Width sensitivity:** three MATLAB meshes compare the directional Oliver width with the element-area width `sqrt(2*A)`. The observed peak-load spreads are 6.19% and 6.80%, respectively, using the same spread definition. This is sensitivity for one geometry, not universal mesh independence.
- **Equivalent-strain sensitivity:** coarse-mesh modified von Mises and maximum-positive-principal options use the same mesh, loading, Oliver width and E, nu, ft, GF. The principal-strain peak is 11.63% higher relative to the modified von Mises peak. That option does not use fc/ft; no claim of improved physical accuracy follows.
- **3D pure tension:** three MATLAB TET4 meshes provide numerical mesh-consistency and equilibrium evidence. No experimental curve is used.
- **Mixed-mode panel and torsion:** these are qualitative MATLAB damage demonstrations. Mixed-mode fields are distinct from the pure-tension mesh study. No Abaqus torsion response is claimed.
- **Timing:** component records describe the observed software/hardware work. Saved MATLAB load-loop times and fresh Abaqus analysis/output times have different boundaries.

## Fixed-increment failures and retries

Baseline 10,000-increment and coarse 2,000-increment Abaqus jobs stopped during equilibrium convergence. Partial converged histories and failure logs are retained. The baseline 20,000-increment retry also failed after 5,174 converged increments (failure during attempt 5,175). Its exact MATLAB reference and failure logs are retained under `reproducibility/fixed_increment_retry/baseline/`; they do not form a complete cross-code comparison. The coarse 4,000-increment comparison completed and passed exact-mesh, schedule, loading-coverage and finite-history checks. No adaptive-increment substitute is used in the current plots.

## Limits of the evidence

Matching increment counts does not make the nonlinear algorithms equivalent. The MATLAB bending solver solves with the preceding damage state, updates damage and records the resulting force imbalance. The UMAT returns degraded elastic stiffness, a secant matrix rather than a consistent damage tangent; Abaqus controls nonlinear equilibrium. A fixed-step convergence failure alone does not prove a material-law bug, and a complete MATLAB history does not imply equal equilibrium accuracy.

The package does not establish experimental 3D validation, universal mesh independence, universal GPU speed advantage or a complete Abaqus assembly/material wall-time partition. The optional hybrid GPU keeps global sparse assembly and factorization on the CPU. The stopped full sparse GPU experiment is not a completed manuscript result.

Separate UMAT timers and native profiles provide partial diagnostics. Timer overhead, unidentified calls and differing timer boundaries remain. See [ABAQUS_TIMING_SCOPE.md](ABAQUS_TIMING_SCOPE.md). Older adaptive, constant-width and larger material-audit records are archival evidence with their original scope.
