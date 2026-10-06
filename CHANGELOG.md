# Changelog

All notable repository changes for FRACMATH are recorded here.

## Current main package - unreleased

- Completed medium/fine MATLAB-Abaqus comparisons on exact paired meshes, with 2,000 fixed increments and -0.1 mm final displacement.
- Three-mesh element-area width `sqrt(2*A)` versus directional Oliver width study.
- Coarse-mesh maximum-positive-principal versus modified von Mises equivalent-strain comparison.
- Ten explained material-point examples as the current manuscript verification suite.
- Current figure reconstruction, native LaTeX/TikZ damage-update flowchart and documented checks.
- Explicit MATLAB/Abaqus timing scopes, partial UMAT/assembly diagnostics and source-based efficiency review.
- Original baseline/coarse fixed-increment failures preserved; baseline 20,000-increment retry also failed after 5,174 converged increments (failure during attempt 5,175). Its diagnostic logs, exact MATLAB reference and frozen source/plan are separate records. The coarse 4,000-increment comparison completed and passed exact-mesh, schedule, loading-coverage and finite-history checks.
- Descriptive mixed-mode panel headings with Nooru-Mohamed benchmark attribution and a separate pure-tension study.

This entry describes the current study companion package. It is not a new release or Zenodo deposit. Earlier release entries below describe archival contents; their adaptive histories, constant-width controls, larger material audits and optional diagnostics are not the current manuscript plots or validation suite.

## 1.1.1 - 2026-10-04

- Complete raw diagnostic records and byte-preserved verification manifests.

## 1.1.0 - 2026-10-04

- Actual UMAT material-point audit and pixel-verified manuscript figure reconstruction.
- Three equilibrium-verified published-geometry 3D meshes and optional dataset-comparison diagnostics; these do not establish experimental validation for the current manuscript.
- Hybrid GPU/CPU and Abaqus SMP comparisons with 90 timing observations.
- Controlled three-mesh comparison with Oliver regularization and a constant reference-width control.
- Structural work, stored energy, damage dissipation, and energy balance histories.
- Load-increment checks and material-point verification in MATLAB and Fortran.
- Exact exported meshes, source hashes, response histories, and Abaqus job diagnostics.
- Operating-system memory measurements and explicitly scoped timing records.
- Reproducibility scripts, implementation guides and shared-color-bar 3D workflow illustrations. Submission paperwork is maintained separately from the software repository.

## 1.0.0 - 2026-05-31

- Initial public software archive for the FRACMATH journal submission.
- Included the 2D three-point bending MATLAB benchmark and Abaqus/UMAT comparison workflow.
- Included the 3D Nooru-Mohamed benchmark.
- Included the 3D notched beam torsion benchmark.
- Included the theory manual, reproducibility guide, citation metadata, and MIT license.
