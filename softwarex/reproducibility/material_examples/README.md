# Ten representative material examples

Each row is one prescribed material-point state, not a structural simulation.

| Case | Purpose |
|---|---|
| 1 | Zero strain |
| 2 | Elastic uniaxial tension |
| 3 | Damaging uniaxial tension |
| 4 | Compression |
| 5 | Pure engineering shear |
| 6 | Equal biaxial strain |
| 7 | Rotated tensile strain and projected width |
| 8 | Unloading from a prescribed damaged tensile state |
| 9 | Reloading beyond the previous strain maximum |
| 10 | Total strain divided between STRAN and DSTRAN |

`case_descriptions.json` lists the exact strain and prior-state inputs. The unchanged production UMAT is compiled with a standalone caller. The production MATLAB material functions are copied verbatim into a material-point caller. Independent tensor calculations provide reference stresses and secant stiffness values. All checked values satisfy `2e-10 + 2e-10 * abs(reference_value)`.

Replay saved outputs from the repository root:

```text
python softwarex/run_material_examples.py --workspace softwarex/reproducibility/material_examples --check
```

Run new examples on the configured MATLAB/Intel Fortran workstation:

```text
python softwarex/run_material_examples.py --workspace C:/runs/material_examples
```

These selected checks explain the implemented equations. They do not establish a consistent damage tangent, universal convergence or experimental validation. Larger archived developer audits are optional and are not the material checks presented in the paper.
