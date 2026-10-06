# FRACMATH

FRACMATH provides vectorized MATLAB continuum-damage calculations, an optional hybrid GPU backend, and an Abaqus user material subroutine (UMAT). The repository contains the software, meshes and numerical records accompanying the SoftwareX article by Jaykumar Mavani and Madura Pathirage, University of New Mexico.

## Version to use

Use the current `main` branch for the SoftwareX package. Download [the current package](https://github.com/Jaykumar9033/FRACMATH/archive/refs/heads/main.zip), or clone the repository and check out `main`. Record the exact commit used. Earlier releases and commits remain archival references; their study packages do not contain all current manuscript companions.

## Quick start

1. Open `softwarex/start_here.m` in MATLAB and press **Run**.
2. The example uses the supplied medium mesh, 2,000 fixed displacement increments, Oliver width and modified von Mises equivalent strain.
3. Read [BEGINNER_GUIDE.md](softwarex/BEGINNER_GUIDE.md) for units, variables and the numerical sequence.

The example writes to a separate results folder. It does not overwrite the numerical archives.

## Requirements

- MATLAB R2024b was used for the recorded simulations.
- The optional hybrid GPU backend requires Parallel Computing Toolbox and a compatible GPU. Global sparse assembly and factorization remain on the CPU.
- Abaqus/Standard 2024 and a configured Intel Fortran compiler are needed only for Abaqus simulations.
- Python analysis and plotting dependencies: `python -m pip install -r requirements.txt`.
- Native LaTeX flowchart compilation requires a TeX installation with TikZ. PDF figure verification requires Poppler's `pdftoppm` on PATH.

## Code and inputs

| Folder or file | Contents |
| --- | --- |
| [3pb/matlab](3pb/matlab/) | Bending solver, material settings and benchmark inputs |
| [3pb/abaqus](3pb/abaqus/) | Plane-stress UMAT, model builder, mesh export and result extraction |
| [Noor mohammad](Noor%20mohammad/) | Pure-tension and mixed-mode panel code and meshes |
| [Torsion](Torsion/) | Torsion example code and meshes |
| [softwarex](softwarex/) | Study runners, current figure scripts and numerical archives |
| [doc](doc/) | Constitutive equations and implementation walkthrough |
| [tests](tests/) | MATLAB smoke checks |

The panel benchmark is attributed to Nooru-Mohamed in the references and source description. Pure-tension and mixed-mode examples have different geometry and loading controls; they are kept distinct.

The bending material settings are E = 37000 MPa, Poisson ratio = 0.20, tensile strength = 3.50 MPa, compressive strength = 35.0 MPa, fracture energy = 0.090 N/mm and thickness = 50 mm. Mesh coordinates and displacement use mm, force uses N and stress uses MPa. Each 3D runner records its own material settings.

See [UMAT_GUIDE.md](softwarex/UMAT_GUIDE.md) for strain input, state variables, projected width and the secant-matrix limitation.

## Current manuscript evidence

| Result | Code and records |
| --- | --- |
| Fixed-increment bending responses | Medium and fine exact meshes; MATLAB and Abaqus each use 2,000 fixed increments to -0.1 mm; `softwarex/reproducibility/fixed_increment_extension/` |
| Damage calculation flowchart | Native TikZ source: `softwarex/figure_sources/damage_update_flowchart.tex` |
| Oliver versus element-area width | Three MATLAB meshes; `h = sqrt(2*A)` versus directional Oliver width; current extension archive |
| Equivalent-strain comparison | Coarse MATLAB mesh; modified von Mises versus maximum positive principal strain; current extension archive |
| Material consistency | Ten explained MATLAB-UMAT states; `softwarex/reproducibility/material_examples/` |
| Pure-tension mesh consistency | Three MATLAB meshes; `softwarex/reproducibility/nooru_25mm_mesh_study/` |
| Mixed-mode panel and torsion | Qualitative MATLAB damage illustrations and supplied geometry sources |
| Timing breakdown | MATLAB saved load-loop components and fresh fixed-increment Abaqus `.msg` records; timing scopes remain different |

From the repository root:

```powershell
python softwarex/plot_current_figures.py --output C:/runs/current_figures
python softwarex/verify_current_figures.py --workspace C:/runs/current_figure_check
```

These scripts reconstruct the current manuscript assets from saved data. They do not run structural simulations. [REPRODUCIBILITY.md](REPRODUCIBILITY.md) and [softwarex/REPRODUCE.md](softwarex/REPRODUCE.md) give the run sequence.

## Interpretation and execution limits

Completed medium/fine comparisons have matching meshes, fixed increment counts and prescribed displacement endpoints. The MATLAB solver updates damage after solving with the preceding damage state and records the post-update residual. Abaqus performs nonlinear equilibrium iterations with a secant UMAT matrix. Matching the schedule does not make these algorithms or their equilibrium accuracy identical.

The original baseline 10,000-increment and coarse 2,000-increment fixed Abaqus jobs failed during convergence. Their converged portions and logs are preserved. The baseline 20,000-increment retry also failed, with 5,174 converged increments (failure during attempt 5,175); its logs and exact MATLAB reference are preserved in `softwarex/reproducibility/fixed_increment_retry/baseline/`. The coarse 4,000-increment comparison completed and passed exact-mesh, schedule, loading-coverage and finite-history checks. No adaptive-increment substitute is used in the current comparison figures.

The area width replaces the constant-width control in the current manuscript. Earlier adaptive-increment, constant-width, hardware-scaling and larger material-check records remain optional archives. They are not the current response plots. The full sparse GPU experiment was stopped and is not a completed manuscript result.

Read [VALIDATION_SCOPE.md](softwarex/VALIDATION_SCOPE.md) before interpreting the results. Numerical mesh consistency is not experimental validation. Partial UMAT and native assembly diagnostics do not allocate complete Abaqus assembly wall time.

## License, citation and support

The code is [MIT licensed](LICENSE). Citation metadata is in [CITATION.cff](CITATION.cff); include the exact commit used. The archival [v1.1.1 core release](https://github.com/Jaykumar9033/FRACMATH/releases/tag/v1.1.1) is available at [DOI 10.5281/zenodo.23138595](https://doi.org/10.5281/zenodo.23138595). Use the current package for the SoftwareX study companions.

Use [GitHub Issues](https://github.com/Jaykumar9033/FRACMATH/issues) for reproducibility questions. Contribution guidance is in [CONTRIBUTING.md](CONTRIBUTING.md).

The CPU bending example also supplies five equivalent-strain definitions: modified von Mises, Mazars, Rankine strain, Rankine stress and smooth Rankine stress. The [controlled comparison](softwarex/EQUIVALENT_STRAIN_STUDY.md) provides formulas, verified histories and Figure 4 reproduction commands.
