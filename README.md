# FRACMATH

FRACMATH is a vectorized MATLAB framework for crack-band regularized continuum damage with a hybrid CPU-GPU implementation and an Abaqus user material subroutine (UMAT). This repository supplies the software and numerical records used in the SoftwareX manuscript by Jaykumar Mavani and Madura Pathirage, University of New Mexico.

## Download and first run

Use the [current release](https://github.com/Jaykumar9033/FRACMATH/releases/tag/current), or clone this repository. Record the exact Git commit used. The `current` label and `main` branch can change; a commit identifies a fixed package.

1. Open `softwarex/start_here.m` in MATLAB and press **Run**.
2. The supplied medium-mesh three-point bending example uses 2,000 increments, Oliver's width and modified von Mises equivalent strain.
3. Read [BEGINNER_GUIDE.md](softwarex/BEGINNER_GUIDE.md) for units, settings and the calculation sequence.

Outputs are written to `softwarex/student_results`. Supplied reference results are preserved. This MATLAB example does not require Abaqus.

## Requirements

- MATLAB R2024b was used for the recorded simulations.
- Hybrid GPU calculations require Parallel Computing Toolbox and a compatible GPU. Sparse assembly and equilibrium solutions remain on the CPU.
- Abaqus/Standard 2024 and configured Intel Fortran are needed for Abaqus examples and fresh UMAT checks.
- Install Python analysis dependencies with `python -m pip install -r requirements.txt`.
- Rebuilding the native flowchart requires TeX with TikZ. PDF figure verification requires Poppler's `pdftoppm`.

## Code and documentation

| Path | Contents |
| --- | --- |
| [3pb](3pb/) | Three-point bending MATLAB and Abaqus code and inputs |
| [Noor mohammad](Noor%20mohammad/) | Nooru-Mohamed geometry and earlier illustrative sources |
| [Torsion](Torsion/) | Torsion code, mesh and geometry resources |
| [softwarex](softwarex/) | Study runners, reference results, figures and instructions |
| [doc](doc/) | Theory reference and implementation walkthrough |
| [tests](tests/) | MATLAB package smoke checks |

Lengths are in mm, forces in N, stresses in MPa and fracture energy in N/mm. Each study records its settings. [NOTATION.md](softwarex/NOTATION.md) maps manuscript symbols to code names.

## Reproduce the manuscript

[REPRODUCIBILITY.md](REPRODUCIBILITY.md) gives an overview; [softwarex/REPRODUCE.md](softwarex/REPRODUCE.md) provides commands.

| Result | Records under `softwarex/reproducibility/` |
| --- | --- |
| Ten material examples | `material_examples/` |
| Matched bending and area/Oliver width comparison | `fixed_increment_extension/` |
| Coarse-mesh 4,000-increment refinement | `fixed_increment_retry/` |
| Two equivalent-strain definitions | `equivalent_strain_study/` |
| Published beam trace and attribution | `experimental_2d/` |
| Current pure-tension mesh study | `unified_softening_20261014/mesh_study/` |
| Completed mixed-mode continuation and half-step check | `unified_softening_20261014/mixed_mode_solver_20261021/` |
| Earlier qualitative mixed-mode images | `nooru_proportional/`; panels in `softwarex/figure_sources/nooru/` |
| Five computing configurations, three timing observations | `scaling_study/` and `timing_repeats/` |

Reconstruct response and damage figures from saved data:

```powershell
python softwarex/plot_current_figures.py --output C:/runs/current_figures
python softwarex/verify_current_figures.py --workspace C:/runs/current_figure_check
```

[SCALING_STUDY.md](softwarex/SCALING_STUDY.md) gives the timing-chart commands. The editable flowchart is `softwarex/figure_sources/damage_update_flowchart.tex`.

## Interpretation

MATLAB's 2D solver updates damage after solving with the previous damage state. Abaqus performs equilibrium iterations with a secant UMAT matrix. Matching meshes and increments does not make their equilibrium accuracy identical. Failed fixed-increment records are retained as diagnostics and excluded from completed comparisons.

Current 3D calculations use the manuscript calibration. Earlier mixed-mode images retained in the paper use an earlier calibration and remain separate qualitative illustrations. No experimental 3D validation is claimed. See [VALIDATION_SCOPE.md](softwarex/VALIDATION_SCOPE.md).

All five timing configurations are retained. MATLAB load-loop time and Abaqus analysis/output wall time cover different work; see [ABAQUS_TIMING_SCOPE.md](softwarex/ABAQUS_TIMING_SCOPE.md).

## License, citation and support

The code is [MIT licensed](LICENSE). [CITATION.cff](CITATION.cff) describes the current package; cite its exact commit. [DOI 10.5281/zenodo.23138595](https://doi.org/10.5281/zenodo.23138595) identifies the earlier numerical-core archive, not the current submission package.

Use [GitHub Issues](https://github.com/Jaykumar9033/FRACMATH/issues) for questions. See [CONTRIBUTING.md](CONTRIBUTING.md) for contributions.
