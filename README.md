# FRACMATH

FRACMATH is a MATLAB finite-element framework for scalar continuum damage with direction-dependent Oliver crack-band regularization. This repository contains the software and reproducible numerical material accompanying the SoftwareX manuscript by Jaykumar Mavani and Madura Pathirage, University of New Mexico.

## Version to use for the SoftwareX article

Use the current `main` branch for the SoftwareX code, meshes, data and reproduction guides. Download [the current package](https://github.com/Jaykumar9033/FRACMATH/archive/refs/heads/main.zip), or clone this repository and check out `main`.

Earlier release downloads and historical commits are archival references. They are superseded as complete SoftwareX reproduction packages: use the current package for the reported figures and studies. For exact reproduction, record the commit you use and follow the immutable companion reference in the manuscript.

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

[REPRODUCIBILITY.md](REPRODUCIBILITY.md) provides run commands. [softwarex/REPRODUCE.md](softwarex/REPRODUCE.md) describes the current paper's studies and archive replay. Figure reconstruction does not require MATLAB or Abaqus licenses.

| Paper result | Code and data |
| --- | --- |
| Figure 1: baseline 2D response and geometry | `softwarex/plot_verified_figures.py`; `softwarex/reproducibility/results_10000/` and `abaqus/` |
| Figure 2: peak/final damage bands | `softwarex/plot_verified_figures.py`; saved 2D states |
| Figure 3: controlled 2D mesh response | `softwarex/analyze_mesh_study.py`; `softwarex/reproducibility/mesh_study/` |
| Figure 4: 3D Nooru-Mohamed examples | `softwarex/analyze_nooru_mesh_study.py`, `softwarex/rebuild_3d_figures.py`; three-mesh pure-tension and mixed-mode archives |
| Figure 5: MATLAB torsion demonstration | `Torsion/working/run_torsion.m`, `softwarex/rebuild_3d_figures.py`; supplied figure sources |
| Figure 6: CPU/GPU/SMP timings | `softwarex/plot_timing_repeats.py`; `softwarex/reproducibility/timing_repeats/` |
| Material-point verification | `softwarex/run_material_examples.py`; ten representative examples |
| Additional UMAT and assembly diagnostics | [Abaqus timing scope](softwarex/ABAQUS_TIMING_SCOPE.md); [phase-timing archive](softwarex/reproducibility/abaqus_phase_timing/README.md) |

From the repository root:

```powershell
python softwarex/analyze_mesh_study.py --output C:/runs/mesh_report --figures C:/runs/mesh_figures
python softwarex/verify_paper_figures.py --workspace C:/runs/fracmath_figure_replay
```

Eight generated assets are compared by pixels; two supplied geometry illustrations are checked by source bytes. Runtime varies between machines and runs.

## Interpretation

The current manuscript reports material-point verification, 2D cross-code and mesh response checks, 3D numerical consistency and hardware timing observations. It does not claim experimental validation or report structural dissipation as a study result. Read [VALIDATION_SCOPE.md](softwarex/VALIDATION_SCOPE.md) for the numerical limits.

The UMAT returns a secant matrix rather than a consistent damage tangent. MATLAB and Abaqus have different increment histories and timing boundaries. Complete Abaqus assembly wall time remains unallocated. The mixed-mode and torsion figures are qualitative; the 3D structural results shown are MATLAB results.

Raw records retain additional checks and diagnostic fields, including the separate 824-case extended material audit. They are preserved for traceability. Submission paperwork is maintained outside this software repository.

## License, citation and support

The code is [MIT licensed](LICENSE). Citation metadata is in [CITATION.cff](CITATION.cff); report the exact commit used for reproduction. The core-source archival [v1.1.1 release](https://github.com/Jaykumar9033/FRACMATH/releases/tag/v1.1.1) is archived at [DOI 10.5281/zenodo.23138595](https://doi.org/10.5281/zenodo.23138595). That archive identifies the numerical core; use the current package for the SoftwareX study companions.

For questions or reproducibility issues, use [GitHub Issues](https://github.com/Jaykumar9033/FRACMATH/issues). Contribution guidance is in [CONTRIBUTING.md](CONTRIBUTING.md).
