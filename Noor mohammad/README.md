# 3D Nooru-Mohamed benchmark

This folder contains the illustrative proportional-loading Nooru-Mohamed
case used in the FRACMATH SoftwareX manuscript. Its archived response is
diagnostic: 894 of 900 increments exceed the equilibrium tolerance. The
separate three-mesh pure-tension numerical consistency study is in
[`softwarex/reproducibility/unified_softening_20261014/mesh_study/`](../softwarex/reproducibility/unified_softening_20261014/README.md).

## Folder map

| Path | Purpose |
| --- | --- |
| `Mesh/` | Main mesh files, MATLAB solver, visualization script, and primary output folder |

## Main workflow

Use the instructions in `Mesh/README.md`.

Short version:

1. Open MATLAB.
2. Change the current folder to `Noor mohammad/Mesh`.
3. Optionally run `visulizaiton` to inspect the mesh and boundary conditions.
4. Run `damage_static('Job-1', opts)` with the options shown in `Mesh/README.md`.

## Main outputs

| Path | Contents |
| --- | --- |
| `Mesh/out_NR_vectorized_LIVE_damage_mesh/` | Primary result CSV, final state, and damage images |

The completed current mixed-mode calculation is separate from these earlier images. Its source, accepted restart and verification are in `../softwarex/reproducibility/unified_softening_20261014/mixed_mode_solver_20261021/`.
