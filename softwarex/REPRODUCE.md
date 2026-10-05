# Reproducing the FRACMATH SoftwareX results

This guide follows the same order as the manuscript. Only the checks used to support manuscript claims are listed first. Additional developer diagnostics are retained in the archive but are not required for the paper.

## 1. Beginner 2D MATLAB run

From the package folder, open MATLAB and run:

```matlab
start_here
```

The preserved reference execution is in `reproducibility/beginner_entry_check/`. To compare the saved arrays with the reference run:

```text
python analyze_beginner_entry.py --workspace reproducibility/beginner_entry_check
```

## 2. Material-point MATLAB-UMAT consistency check

This is a constitutive check at a material integration point, not a one-element structural finite-element analysis. The same prescribed material states are evaluated by the MATLAB constitutive functions and the unchanged Abaqus UMAT.

Replay the archived 712-case comparison:

```text
python audit_umat.py --workspace reproducibility/umat_audit --check
```

The archive records the input states, UMAT outputs, MATLAB outputs and maximum differences. A checked value passes when its absolute difference is no greater than `2e-10 + 2e-10 * abs(reference_value)`.

## 3. Baseline 2D MATLAB-Abaqus benchmark

The baseline MATLAB histories are stored in `reproducibility/results_1000/` and `reproducibility/results_10000/`. The 10,000-step history is used for the main MATLAB curve.

For Abaqus, from `reproducibility/abaqus/` run the supplied no-GUI builder with a licensed Abaqus installation. The script rebuilds the model, writes the Oliver shape-function-gradient table and extracts the load-CMOD response.

The MATLAB and Abaqus solvers use different equilibrium/increment procedures, so the manuscript compares structural response curves, damage fields and constitutive consistency rather than matching iteration counts.

## 4. Controlled 2D mesh/regularization study

The archived study is in `reproducibility/mesh_study/`. Reanalyze the completed runs and rebuild the four-panel mesh figure with:

```text
python analyze_mesh_study.py --workspace reproducibility/mesh_study
```

The current manuscript uses:

- coarse, medium and fine load-CMOD curves,
- Oliver-width versus constant-width response,
- Abaqus/UMAT mesh responses,
- the fine-mesh MATLAB-Abaqus comparison,
- peak-load spread and increment sensitivity.

Energy/dissipation histories may exist in the raw solver folders as developer diagnostics, but they are not used as manuscript results.

## 5. 3D pure-tension numerical consistency

Run:

```text
python analyze_nooru_mesh_study.py --workspace reproducibility/nooru_25mm_mesh_study --require-all
```

This checks the three completed published-geometry TET4 histories and rebuilds the pure-tension comparison figure. The result is a numerical mesh-consistency/equilibrium check, not experimental validation.

## 6. Qualitative 3D examples

The proportional mixed-mode archive is in `reproducibility/nooru_proportional/`. Its damage images are used only as a qualitative illustration.

The torsion figure is generated from the MATLAB/FRACMATH torsion workflow. No Abaqus 3D torsion response is used in the paper.

## 7. Rebuild manuscript figures

To rebuild and compare the generated manuscript assets in a separate workspace:

```text
python verify_paper_figures.py --workspace ./figure_replay_check
```

## Optional developer archives

`reproducibility/umat_precision/`, detailed Abaqus profiling folders, and energy/dissipation histories are retained for software development and auditability. They are not required for the manuscript's main scientific claims.
