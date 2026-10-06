# A first run and a guide to the code

## Run the supplied example

Use the extracted submission folder as the package root. In the GitHub repository, first enter the `softwarex` folder.

1. Open `start_here.m` in MATLAB R2024b.
2. Leave `number_of_steps = 2000`, `backend = 'cpu'`, and `number_of_threads = 1` for the supplied medium-mesh example. Its final prescribed displacement is -0.1 mm.
3. Press **Run**. The mesh is supplied; no Abaqus license is needed for this MATLAB example.
4. Open `student_results/matlab_load_cmod.csv` for crack opening and load, and `verified_state.mat` for the saved numerical arrays.

Set `show_figures = false` when measuring computing time. Set `run_material_test = true` to run the short material check instead of a structural simulation. The GPU option requires Parallel Computing Toolbox and a supported GPU; CPU is the default. Results have a separate folder so the paper's archived data remain available.

`start_here.m` explicitly sets the mesh, displacement, regularization, equivalent-strain option, thread and backend controls. The example uses Oliver width and modified von Mises equivalent strain. Material constants are listed near the top of `solver_main_3pb.m`. The entry script passes settings to that solver; there is one implementation of the numerical solver.

## Units and variables

Length is in mm, force is in N, stress is in MPa, and fracture energy is in N/mm. Strain and damage are dimensionless. Let `nN` be the number of nodes and `nE` the number of triangles.

| Variable | Size | Meaning |
|---|---|---|
| `nodes` | `nN x 2` | Node coordinates, x and y |
| `elems` | `nE x 3` | Three node numbers for each triangle |
| `u` | `2*nN x 1` | Alternating x and y nodal displacements |
| `B_all` | `3 x 6 x nE` | Maps six element displacements to `[ex, ey, gxy]` |
| `gradN_all` | `nE x 6` | `[g1x, g1y, g2x, g2y, g3x, g3y]` shape-function gradients |
| `Ke0` | `6 x 6 x nE` | Elastic element stiffness before damage |
| `K` | `2*nN x 2*nN`, sparse | Global stiffness matrix |
| `omega` | `nE x 1` | Damage: zero is intact, values near one are highly damaged |
| `kappa` | `nE x 1` | Largest equivalent strain previously reached |
| `F`, `CMOD` | one value per increment | Reaction load and crack-mouth opening |

MATLAB's `.*`, `./`, and `.^` act separately on each array entry. `pagemtimes` applies matrix multiplication to each element page. These operations evaluate the same element formulas together, reducing MATLAB loop overhead.

## Read the solver in this order

1. **Parameters and mesh:** read the material constants, mesh, support nodes, loading nodes, and two CMOD points.
2. **Element data:** `precompute_T3` calculates triangle areas, shape-function gradients, strain operators, and element displacement indices. Elastic matrices are computed once.
3. **One displacement increment:** `assemble_K` multiplies each elastic stiffness by `1 - omega` and adds its entries to a sparse global matrix. `factor_free_stiffness` factors the free-displacement block. The inner loop solves with the previous damage held fixed.
4. **Damage calculation:** `damage_update` obtains element strains, principal strain direction, equivalent strain, projected width, and irreversible damage/history.
5. **Record the response:** the solver assembles the new damaged stiffness, calculates reaction and CMOD, records the residual, and saves the numerical arrays used for the response plots.

The old-damage equilibrium solve and the subsequent damage calculation are distinct operations. The solver reports the remaining free-node residual after damage changes; the inner loop's convergence flag does not imply equilibrium after that change.

## How crack-band regularization enters the code

For each triangle, project its three shape-function gradients onto the maximum-principal-strain direction `n`. The width is `h = 2 / sum(abs(gradN * n))`. The softening parameter is then `eps_f = eps0/2 + GF/(h*ft)`. The history is `max(kappa_old, equivalent_strain)`, and damage cannot decrease on unloading.

The width changes with direction. The current manuscript compares it with `h = sqrt(2*A)`, where `A` is the area of each triangle. This area width follows element size but does not change with the strain direction. The two choices are compared on the same coarse, medium and fine meshes. A constant-width option remains only to reproduce older archives.

The current coarse-mesh CPU comparison uses three damage drivers: modified von Mises, elastic energy and Rankine stress. Figure 4 shows load versus CMOD. All use the same mesh, 2,000 fixed increments, Oliver width formula, tensile onset and exponential energy calibration. These are scalar-driver alternatives within the same damage update, not complete independently calibrated concrete models. Only modified von Mises uses fc/ft. The total-energy definition also activates in compression and is not calibrated to fc. See [EQUIVALENT_STRAIN_STUDY.md](EQUIVALENT_STRAIN_STUDY.md) for formulas, checks and reproduction commands.

## CPU, hybrid GPU, and Abaqus

Read the CPU branch first. The optional `gpu_damage_point` function is the scalar version of the same damage formula. `gpuArray.arrayfun` evaluates it across elements. Global sparse assembly and factorization remain on the CPU, so this is a hybrid implementation.

The area-width and alternative equivalent-strain options are verified on CPU. GPU requests for these options are rejected until that path is tested. The hybrid kernel retains the existing modified-von-Mises formulation.

MATLAB's eight-thread setting is a limit for supported numerical libraries. It is not eight independent simulations. Abaqus can use SMP threads and initializes the gradient table before material calls. The completed medium/fine manuscript comparisons use the same exact mesh, 2,000 fixed increments and -0.1 mm final prescribed displacement in each pair. Abaqus's equilibrium algorithm differs from MATLAB's sequential update.

The original baseline and coarse fixed Abaqus cases stopped during convergence; their partial histories are preserved. The baseline 20,000-increment retry also failed, with 5,174 converged increments (failure during attempt 5,175); its diagnostic record is in `reproducibility/fixed_increment_retry/baseline/`. The coarse 4,000-increment comparison completed and passed exact-mesh, schedule, loading-coverage and finite-history checks. A complete MATLAB history does not imply that every point meets Abaqus's equilibrium criterion, and failed fixed cases are not replaced by adaptive histories.

## What can reproduce exactly?

With identical inputs, software, backend, and numerical settings, saved numerical arrays can be compared directly. Compare `F`, `CMOD`, `omega`, `kappa`, and displacement histories. Repeated-run checks report exact equality separately from tolerance-based agreement.

Different CPU/GPU arithmetic can produce small floating-point differences. GPU and CPU curves are checked using declared tolerances, not promised to match bit for bit. Runtime, memory use, video compression, file timestamps, MAT-file headers, and image/PDF metadata are not exact numerical outputs.

For the current manuscript figures, use `plot_current_figures.py`. It reads the completed fixed-increment extension and the supplied 3D sources. The editable numerical flowchart is in `figure_sources/damage_update_flowchart.tex`. Earlier baseline and hardware-study figure scripts remain archive replay tools.

For the Fortran material routine, follow the seven steps in
[UMAT_GUIDE.md](UMAT_GUIDE.md). The guide explains how total strain,
crack-band width, damage and stress are calculated, and why the secant
matrix can lead to additional Abaqus iterations.

Run `verify_current_figures.py --workspace C:/runs/figure_replay` with Python
to check all manuscript figure assets in a separate folder. The three-mesh
pure-tension comparison uses the completed published-geometry archive;
mixed-mode damage images remain qualitative.

## Words used in the code

| Word | Simple meaning |
| --- | --- |
| Node | A point in the mesh with an unknown displacement |
| Element | A triangle in 2D or a tetrahedron in 3D |
| Degree of freedom (DOF) | One displacement component at one node |
| Boundary condition | A displacement or force specified by the test |
| Assembly | Adding all element stiffness contributions into one matrix |
| Sparse matrix | A matrix that stores mainly its nonzero entries |
| Factorization | Preparing a matrix so the displacement equations can be solved |
| Residual | The force imbalance left after a trial solution |
| Secant stiffness | Elastic stiffness reduced by the current damage |
| Increment | One small change in the applied displacement or load |
| History variable | A stored value from earlier loading; here the largest equivalent strain |
| CMOD | The relative displacement of two nodes across the notch mouth |

## Follow one triangle

Start with the CPU branch in `damage_update`. The code takes the six displacement components of a triangle and multiplies them by its `B` matrix. This gives normal strains `ex`, `ey` and engineering shear strain `gxy`. The shear entry of the strain tensor is `gxy/2`.

The principal strains describe extension and compression along special directions. The equivalent strain combines them into one scalar. `kappa` stores the largest equivalent strain reached, so unloading does not erase the loading history. The projected width sets the softening scale. `omega` then reduces the element stiffness through `1 - omega`.

For a single element, the assembly idea is:

```matlab
% This explains the formula; it is not a second solver.
element_stiffness = (1 - element_damage) * elastic_stiffness;
```

The production code evaluates many element matrices together. `sparse` adds contributions with the same row and column. Reading the single-element formula first helps explain the vectorized statements.

## Which files should I read next?

1. `start_here.m`: choose a run and find its output folder.
2. `solver_main_3pb.m`: read the numbered sections, then `load_mesh`, `precompute_T3`, `assemble_K` and `damage_update`.
3. `UMAT_GUIDE.md`: match the MATLAB material variables to the Fortran variables.
4. `MESH_STUDY.md` and `COMPARISON_EXTENSION.md`: understand the mesh, width and fixed-increment choices before running the study.
5. `ABAQUS_TIMING_SCOPE.md`: understand the timer limits. `SCALING_STUDY.md` describes optional earlier hardware observations.
6. `plot_current_figures.py`: see how saved numerical arrays become current manuscript plots. This script does not solve the model.

The `run_*.py` scripts organise simulations. The `analyze_*.py` scripts read saved results. The `plot_*.py` scripts draw figures. `run_material_examples.py` checks the ten material examples; `verify_current_figures.py` checks current figure reconstruction. Exact commands are in `REPRODUCE.md`.

## Reading the 3D examples

The panel helper `Noor mohammad/Mesh/damage_static.m` reads a mesh prefix and an `opts` structure. Nooru-Mohamed is the source benchmark attribution. A structure groups named settings such as `E`, `GF` and `nIncr`. The local helper uses a supplied setting when it exists and otherwise uses the default. Read material, loading and convergence settings before the element calculations. The pure-tension case and the qualitative mixed-mode panel use different loading controls and notch geometry.

`Torsion/working/run_torsion.m` sets the material and loading geometry, then passes its `opts` structure to the 3D calculation. Three-dimensional strain and stiffness arrays are larger than in the triangle example. Read the 2D example first. The mixed-mode and torsion damage fields have the validation limits described in `VALIDATION_SCOPE.md`.

## Common first-run problems

- Missing mesh file: keep the downloaded folder structure intact.
- GPU function is unavailable: leave `backend = 'cpu'`.
- No live plot: check `show_figures`; numerical outputs can still be saved.
- Different settings give a different curve: record the mesh, material, increments and backend before comparing outputs.
- A slow run: first use CPU and headless output. Timing depends on hardware; it is not an exact reproduction target.
