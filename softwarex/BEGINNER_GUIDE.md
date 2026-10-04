# A first run and a guide to the code

## Run the supplied example

1. Open `softwarex/start_here.m` in MATLAB R2024b.
2. Leave `number_of_steps = 10000`, `backend = 'cpu'`, and `number_of_threads = 1` for the Figure 1 settings.
3. Press **Run**. The mesh is supplied; no Abaqus license is needed for this MATLAB example.
4. Open `softwarex/student_results/matlab_load_cmod.csv` for crack opening and load, and `verified_state.mat` for the saved numerical arrays.

Set `show_figures = false` when measuring computing time. Set `run_material_test = true` to run the short material check instead of a structural simulation. The GPU option requires Parallel Computing Toolbox and a supported GPU; CPU is the default. Results have a separate folder so the paper's archived data remain available.

`start_here.m` explicitly sets the size, displacement, regularization, thread, and backend controls used by this example. Material constants are listed near the top of `solver_main_3pb.m`. The entry script passes settings to that solver; there is one implementation of the numerical solver.

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
5. **Record the response:** the solver assembles the new damaged stiffness, calculates reaction and CMOD, records the residual and energy diagnostics, and saves arrays.

The old-damage equilibrium solve and the subsequent damage calculation are distinct operations. The solver reports the remaining free-node residual after damage changes; the inner loop's convergence flag does not imply equilibrium after that change.

## How crack-band regularization enters the code

For each triangle, project its three shape-function gradients onto the maximum-principal-strain direction `n`. The width is `h = 2 / sum(abs(gradN * n))`. The softening parameter is then `eps_f = eps0/2 + GF/(h*ft)`. The history is `max(kappa_old, equivalent_strain)`, and damage cannot decrease on unloading.

The width changes with the direction. Replacing it with the fixed reference width provides the paper's control calculation. Material-point energy checks test this formula locally; the structural mesh study measures its effect for one bending geometry.

## CPU, hybrid GPU, and Abaqus

Read the CPU branch first. The optional `gpu_damage_point` function is the scalar version of the same damage formula. `gpuArray.arrayfun` evaluates it across elements. Global sparse assembly and factorization remain on the CPU, so this is a hybrid implementation.

MATLAB's eight-thread setting is a limit for supported numerical libraries. It is not eight independent simulations. Abaqus uses eight SMP threads, initializes the gradient table before material calls, and uses the same mesh and material parameters. Its equilibrium algorithm differs from MATLAB's sequential update.

## What can reproduce exactly?

With identical inputs, software, backend, and numerical settings, saved numerical arrays can be compared directly. Compare `F`, `CMOD`, `omega`, `kappa`, displacement, and energy histories. Repeated-run checks report exact equality separately from tolerance-based agreement.

Different CPU/GPU arithmetic can produce small floating-point differences. GPU and CPU curves are checked using declared tolerances, not promised to match bit for bit. Runtime, memory use, video compression, file timestamps, MAT-file headers, and image/PDF metadata are not exact numerical outputs.

For archived paper figures, use `plot_verified_figures.py` and `rebuild_3d_figures.py`. Keep the 10,000-step history for Figure 1. The separate 2,000-step hardware study has different settings and does not replace it.

For the Fortran material routine, follow the seven steps in
[UMAT_GUIDE.md](UMAT_GUIDE.md). The guide explains how total strain,
crack-band width, damage and stress are calculated, and why the secant
matrix can lead to additional Abaqus iterations.

Run `verify_paper_figures.py --workspace C:/runs/figure_replay` with Python
to check all manuscript figure assets in a separate folder. The three-mesh
pure-tension comparison uses the completed published-geometry archive;
mixed-mode damage images remain qualitative.
