# Bending mesh and regularization study

## Purpose

The current study asks how bending load-CMOD curves change with mesh density and with crack-band width, and whether MATLAB/Abaqus responses agree when the mesh and prescribed increment schedule match. Structural dissipation is not a reported manuscript result.

## Exact mesh family

Coarse, medium and fine meshes are retained under `reproducibility/mesh_study/` and copied with hashes into `reproducibility/fixed_increment_extension/`. Geometry, support nodes, loading strip and CMOD nodes are preserved. Each current width-study pair uses the same mesh, material parameters, 2,000 fixed increments and final prescribed displacement of -0.1 mm.

## Width choices

- `oliver`: project the triangle's shape-function gradients onto its maximum-principal-strain direction. The width is `h = 2 / sum(abs(gradN * n))`.
- `area`: use `h = sqrt(2*A)` separately for every triangle, where A is its area in square millimetres.

The area width follows element size but does not change with strain direction. Oliver width accounts for direction and element geometry. Both enter the same bending softening calibration, `eps_f = eps0/2 + GF/(h*ft)`.

A constant 1.25 mm control is retained only for historical archive replay; it is not the current manuscript width comparison.

## Completed MATLAB results

| Mesh | Oliver peak load (N) | Area-width peak load (N) |
| --- | ---: | ---: |
| Coarse | 4193.718 | 4113.115 |
| Medium | 4205.029 | 4122.738 |
| Fine | 4458.989 | 4399.661 |

The peak-load spread is 6.19% for Oliver and 6.80% for area width. These observations support a numerical sensitivity discussion for this geometry; they do not establish general mesh independence or select a universally better width.

## Fixed-increment Abaqus comparison

Medium and fine Abaqus cases complete 2,000 fixed increments on the exact corresponding MATLAB meshes, to the same -0.1 mm endpoint. ODB times and loading displacement are checked rather than inferred from row count. The current response plots use these completed cases.

The original coarse 2,000-increment and baseline 10,000-increment Abaqus jobs failed during convergence. Their partial curves and logs are preserved. The baseline 20,000-increment retry also failed after 5,175 accepted increments recorded in `.sta`; its logs and exact MATLAB reference are retained in `reproducibility/fixed_increment_retry/baseline/`. The coarse 4,000-increment retry is running and requires final verification before use as a complete comparison. There is no adaptive substitution.

## Reconstruct the current plots

From the repository root:

```powershell
python softwarex/plot_current_figures.py --output C:/runs/current_figures
python softwarex/verify_current_figures.py --workspace C:/runs/current_figure_check
```

Read `COMPARISON_EXTENSION.md` before starting fresh simulations. The original `analyze_mesh_study.py` and four-panel `mesh_study_overview` assets belong to the archived Oliver/constant-width study.

## Interpretation

MATLAB updates damage after solving with its preceding state and records the post-update residual. Abaqus performs nonlinear equilibrium iterations with the UMAT's secant matrix. Identical mesh and fixed increments improve comparability but do not make the nonlinear algorithms or accuracy criteria identical. Runtime and peak differences must be interpreted with those limits.
