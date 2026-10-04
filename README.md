# FRACMATH

FRACMATH is a MATLAB finite-element framework for scalar continuum damage with direction-dependent Oliver crack-band regularization. This repository contains the software and reproducible numerical material accompanying the SoftwareX manuscript by Jaykumar Mavani and Madura Pathirage, University of New Mexico.

## Quick start

1. Download or clone this repository.
2. Open `softwarex/start_here.m` in MATLAB and press **Run**.
3. Read [BEGINNER_GUIDE.md](softwarex/BEGINNER_GUIDE.md) for settings, units, outputs and the numerical sequence.

The supplied meshes are ready to use. The beginner script uses the paper solver and writes to a separate results folder.

## Requirements

- MATLAB R2024b was used for the recorded simulations.
- The optional hybrid GPU backend requires Parallel Computing Toolbox and a compatible GPU. Sparse factorization remains on the CPU.
- Abaqus/Standard 2024 and a configured Intel Fortran compiler are required only for Abaqus simulations.
- Python dependencies for archived-data analysis and plotting: `python -m pip install -r requirements.txt`.
- Figure pixel verification also requires Poppler's `pdftoppm` on PATH.

## Code and inputs

| Folder or file | Contents |
| --- | --- |
| [3pb/matlab](3pb/matlab/) | 2D solver, material parameters, mesh, boundary conditions and reference results |
| [3pb/abaqus](3pb/abaqus/) | UMAT, Abaqus job builder, mesh export and result extraction |
| [Noor mohammad](Noor%20mohammad/) | 3D tension and mixed-mode example code and meshes |
| [Torsion](Torsion/) | 3D torsion example code and meshes |
| [softwarex](softwarex/) | Study runners, analysis scripts, plotting scripts and reference data |
| [doc](doc/) | Constitutive equations and implementation walkthrough |
| [tests](tests/) | MATLAB smoke checks |

### Material parameters

The primary 2D benchmark uses E = 37000 MPa, Poisson ratio = 0.20, tensile strength = 3.50 MPa, compressive strength = 35.0 MPa and fracture energy = 0.090 N/mm. These values and the 50 mm thickness are set near the top of [solver_main_3pb.m](3pb/matlab/solver_main_3pb.m). Each study runner and archived input records its own parameters; these defaults must not be assumed for every 3D example. Mesh coordinates and displacement use mm, force uses N, and stress uses MPa.

See [UMAT_GUIDE.md](softwarex/UMAT_GUIDE.md) for state variables, the material sequence, projected width and the secant-matrix limitation.

## Reproduce the paper results

[REPRODUCIBILITY.md](REPRODUCIBILITY.md) gives simulation commands. [softwarex/REPRODUCE.md](softwarex/REPRODUCE.md) gives archive and figure instructions. Archived-data plotting can be performed without MATLAB or Abaqus licenses.

| Paper result | Data and instructions |
| --- | --- |
| Figure 1: 2D response and geometry | `softwarex/reproducibility/results_10000/`, `softwarex/reproducibility/abaqus/`; `plot_verified_figures.py` |
| Figure 2: peak/final damage bands with mesh | Same archived 2D states; `plot_verified_figures.py` |
| Figure 3: Nooru numerical response and damage | `softwarex/reproducibility/nooru_25mm_mesh_study/`, `softwarex/figure_sources/`; `analyze_nooru_mesh_study.py`, `rebuild_3d_figures.py` |
| Figure 4: torsion damage example | `softwarex/figure_sources/`; `rebuild_3d_figures.py` |
| Figure 5: structural mesh sensitivity | `softwarex/reproducibility/mesh_study/`; `analyze_mesh_study.py` |
| MATLAB and Abaqus timing tables | `compare_solver_diagnostics.py`; [timing scope](softwarex/ABAQUS_TIMING_SCOPE.md) |
| CPU and hybrid GPU comparisons | [SCALING_STUDY.md](softwarex/SCALING_STUDY.md); `softwarex/reproducibility/timing_repeats/` |
| Material and UMAT verification | `audit_umat.py`; [824-case precision archive](softwarex/reproducibility/umat_precision/README.md) |
| Additional UMAT and assembly measurements | [Abaqus phase-timing archive](softwarex/reproducibility/abaqus_phase_timing/README.md) |

Run from the repository root:

```powershell
python softwarex/compare_solver_diagnostics.py
python softwarex/analyze_mesh_study.py
python softwarex/run_umat_precision.py --workspace softwarex/reproducibility/umat_precision --analyze-only
python softwarex/verify_paper_figures.py --workspace C:/runs/fracmath_figure_replay
```

Verification compares seven generated assets by pixels and two supplied geometry illustrations by source bytes. Numerical reproduction concerns response and state arrays; elapsed times vary between machines and executions.

## Interpretation

Read [VALIDATION_SCOPE.md](softwarex/VALIDATION_SCOPE.md) for measured scopes and limitations. The UMAT returns a degraded elastic secant matrix. MATLAB and Abaqus use different iteration histories and timing scopes. Hybrid GPU speedup was not observed on the tested workstation. The 3D mixed-mode and torsion fields are qualitative examples. Failed numerical checks remain documented where they qualify the reported evidence.

Raw solver logs, input files, source snapshots and SHA256 manifests are retained as scientific evidence. Submission paperwork and temporary document-build files are maintained outside this software repository.

## License, citation and support

The code is [MIT licensed](LICENSE). Citation metadata is in [CITATION.cff](CITATION.cff); report the exact commit used for reproduction. The existing [v1.1.1 release](https://github.com/Jaykumar9033/FRACMATH/releases/tag/v1.1.1) is archived at [DOI 10.5281/zenodo.23138595](https://doi.org/10.5281/zenodo.23138595). Additional study evidence is identified separately in the manuscript.

For questions or reproducibility issues, use [GitHub Issues](https://github.com/Jaykumar9033/FRACMATH/issues). Contribution guidance is in [CONTRIBUTING.md](CONTRIBUTING.md).
