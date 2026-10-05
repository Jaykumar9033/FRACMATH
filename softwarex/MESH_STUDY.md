# Controlled 2D mesh and regularization study

## Purpose

This study answers two manuscript questions:

1. How sensitive is the 2D load-CMOD response to mesh refinement when the direction-dependent Oliver crack-band width is used?
2. Do MATLAB and Abaqus/UMAT give comparable structural responses on the same controlled meshes?

The manuscript does **not** use dissipation as a study result.

## Mesh family

Three exported meshes are retained under `reproducibility/mesh_study/`: coarse, medium and fine. Geometry, support locations, loading strip and CMOD measurement points are checked so that only mesh density and the selected regularization treatment change.

## MATLAB cases

For each mesh, two MATLAB responses are retained:

- `oliver`: the projected crack-band width is computed from element shape-function gradients and the current principal-strain direction;
- `fixed`: a constant reference width of 1.25 mm is used as a control.

The main response quantity is load versus crack-mouth opening displacement (CMOD). Additional raw diagnostic files written by the solver are preserved but are not used in the manuscript discussion.

## Abaqus cases

The Abaqus cases use the same exported mesh family and the corresponding UMAT. The analysis script checks that the Oliver gradient table is loaded for the expected number of elements and reads the extracted load-CMOD histories.

## Analysis

From the package root run:

```text
python analyze_mesh_study.py --workspace reproducibility/mesh_study
```

The script checks response validity, mesh/BC consistency, peak load, peak CMOD, post-update residuals, increment sensitivity and MATLAB-Abaqus peak differences. It rebuilds:

- `figures/mesh_study_overview.pdf`
- `figures/mesh_study_overview.png`

The four panels show:

(a) MATLAB with Oliver regularization;
(b) MATLAB with fixed width;
(c) Abaqus/UMAT with Oliver regularization;
(d) fine-mesh MATLAB-Abaqus response comparison.

## Interpretation

This is a controlled numerical sensitivity study for one benchmark geometry. It does not prove general mesh independence, and it does not use structural dissipation as a manuscript conclusion.
