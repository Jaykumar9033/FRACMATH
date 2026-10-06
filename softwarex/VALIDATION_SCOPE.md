# Validation and verification scope

FRACMATH implements established continuum-damage and crack-band methods. The article checks the software implementation and numerical behavior; it does not introduce a new constitutive theory.

## What is checked

- **Material point:** ten prescribed states compare MATLAB, the actual Abaqus UMAT and independent reference calculations. The permitted difference is `2e-10 + 2e-10 * abs(reference_value)`. These are not one-element structural analyses.
- **Matched fixed increments:** completed medium/fine bending cases use identical meshes, 2,000 fixed increments and -0.1 mm final displacement in MATLAB and Abaqus. Actual ODB times and loading displacement are checked; load-CMOD curves provide structural response comparisons.
- **Width sensitivity:** three MATLAB meshes compare the directional Oliver width with the element-area width `sqrt(2*A)`. The observed peak-load spreads are 6.19% and 6.80%, respectively, using the same spread definition. This is sensitivity for one geometry, not universal mesh independence.
- **Equivalent-strain sensitivity:** The current coarse-mesh CPU comparison uses modified von Mises, elastic energy and Rankine stress. Figure 4 shows load versus CMOD. All use the same mesh, 2,000 fixed increments, Oliver width formula, tensile onset and exponential energy calibration. These are scalar-driver alternatives within the same damage update, not complete independently calibrated concrete models. Only modified von Mises uses fc/ft. The total-energy definition also activates in compression and is not calibrated to fc. See [EQUIVALENT_STRAIN_STUDY.md](EQUIVALENT_STRAIN_STUDY.md) for formulas, checks and reproduction commands.
- **Published 2D experiment:** Figure 4 includes the `experiments 100 mm` trace from Grassl et al. (2012), Figure 5. Nominal depth/thickness/span/length/notch depth are 100/50/250/350/20 mm. The recovered vertices are published graphic coordinates, not raw laboratory samples. Exact experimental notch width, loading control and replicate identity are unverified; no material fitting is performed. The display covers CMOD 0–0.16 mm, while the full recovered trace reaches 0.3363 mm. See [experimental_2d](reproducibility/experimental_2d/README.md).
- **3D pure tension:** three MATLAB TET4 meshes provide numerical mesh-consistency and equilibrium evidence. No experimental curve is used.
- **Mixed-mode panel and torsion:** these are qualitative MATLAB damage demonstrations. Mixed-mode fields are distinct from the pure-tension mesh study. No Abaqus torsion response is claimed.
- **Timing:** component records describe the observed software/hardware work. Saved MATLAB load-loop times and fresh Abaqus analysis/output times have different boundaries.

## Fixed-increment failures and retries

Baseline 10,000-increment and coarse 2,000-increment Abaqus jobs stopped during equilibrium convergence. Partial converged histories and failure logs are retained. The baseline 20,000-increment retry also failed after 5,174 converged increments (failure during attempt 5,175). Its exact MATLAB reference and failure logs are retained under `reproducibility/fixed_increment_retry/baseline/`; they do not form a complete cross-code comparison. The coarse 4,000-increment comparison completed and passed exact-mesh, schedule, loading-coverage and finite-history checks. No adaptive-increment substitute is used in the current plots.

## Limits of the evidence

Matching increment counts does not make the nonlinear algorithms equivalent. The MATLAB bending solver solves with the preceding damage state, updates damage and records the resulting force imbalance. The UMAT returns degraded elastic stiffness, a secant matrix rather than a consistent damage tangent; Abaqus controls nonlinear equilibrium. A fixed-step convergence failure alone does not prove a material-law bug, and a complete MATLAB history does not imply equal equilibrium accuracy.

The package does not establish experimental 3D validation, universal mesh independence, universal GPU speed advantage or a complete Abaqus assembly/material wall-time partition. The optional hybrid GPU keeps global sparse assembly and factorization on the CPU. The stopped full sparse GPU experiment is not a completed manuscript result.

Earlier UMAT timers and native profiles are optional developer archives, not current manuscript timing results. The current table reports matched-run MATLAB components and Abaqus message-file solver/total times with an unallocated remainder. See [ABAQUS_TIMING_SCOPE.md](ABAQUS_TIMING_SCOPE.md). Older adaptive, constant-width and larger material-audit records are archival evidence with their original scope.
