# Five equivalent-strain definitions

Figure 4 compares five scalar damage drivers in the MATLAB plane-stress
bending example. These are alternative equivalent-strain definitions used
inside the same FRACMATH history and exponential damage update. Selecting
Mazars equivalent strain does not implement the complete Mazars concrete
model with separate tensile/compressive damage functions.

## Definitions

Let `e1,e2,e3` be the elastic principal strains, including the recovered
plane-stress component `e3 = -nu/(1-nu)*(ex+ey)`. Define the undamaged
principal stresses by isotropic elasticity. Their dimensionless values are

`qi = sigma_i^0/E = ei/(1+nu) + nu*I1/((1+nu)*(1-2*nu))`,

where `I1 = e1+e2+e3`. Positive brackets mean `max(value,0)`.

| Setting | Figure label | Equivalent strain |
| --- | --- | --- |
| `modified_mises` | Modified von Mises | Existing de Vree invariant expression, using `I1`, `J2` and `k=fc/ft` |
| `rankine` | Rankine (strain) | `max(e1,e2,e3,0)` |
| `mazars` | Mazars | `sqrt(max(e1,0)^2 + max(e2,0)^2 + max(e3,0)^2)` |
| `rankine_stress` | Rankine (stress) | `max(q1,q2,q3,0)` |
| `smooth_rankine_stress` | Smooth Rankine (stress) | `sqrt(max(q1,0)^2 + max(q2,0)^2 + max(q3,0)^2)` |

Stress-based and strain-based Rankine definitions are distinct under
multiaxial loading. Smooth Rankine based on positive principal strain is
the same norm as Mazars here, so it is not counted as a sixth distinct case.

The four tensile alternatives do not use `fc/ft`. Under free uniaxial
compression, strain Rankine gives `nu*abs(ex)` and Mazars gives
`sqrt(2)*nu*abs(ex)` because of lateral extension. The stress-based measures
give zero for this path. All five reproduce the same equivalent strain
under free uniaxial tension. These differences must be considered when
choosing and calibrating a criterion for concrete.

## Controlled simulation settings

Every run uses the same exact coarse CPS3 mesh, 2,000 fixed increments,
final prescribed displacement -0.1 mm, CPU with one thread, Oliver width,
and the same E, nu, ft, GF and exponential softening calibration. Only the
equivalent-strain definition changes. The width formula remains identical;
its values can differ as the predicted strain direction changes.

The runner first checks ten material states with an independent tensor
eigensolve for each criterion. It also checks tensile onset, four widths,
uniaxial fracture energy and unloading/reloading. Structural checks inspect
exact mesh identity, increment sequence, final loading extent, finite
states, damage bounds and the saved post-update force residual.

These are implementation and sensitivity checks. They do not establish
experimental accuracy, identical multiaxial strength envelopes or a fully
coupled nonlinear equilibrium solution. Alternative definitions are CPU-only;
the previously verified hybrid GPU kernel retains modified von Mises.
The Abaqus UMAT remains the default modified-von-Mises/Oliver implementation.

## Results

| Driver | Peak load [kN] | Peak change from modified von Mises |
| --- | ---: | ---: |
| Modified von Mises | 4.194 | +0.00% |
| Rankine (strain) | 4.681 | +11.63% |
| Mazars | 4.689 | +11.82% |
| Rankine (stress) | 4.781 | +13.99% |
| Smooth Rankine (stress) | 4.773 | +13.81% |

All five complete 2,000 increments and reach -0.1 mm prescribed displacement. The Mazars load-CMOD path reverses during later loading; points are retained in loading order. A single-valued common-CMOD RMS is therefore not reported for this case. The companion `equivalent_strain_load_displacement` plot uses the monotone prescribed displacement and helps interpret that path. No claim of experimental accuracy follows from the higher peaks.

The maximum post-damage relative residual ranges from 1.08% to 1.82% across these sequential-secant runs. The preceding-damage linear equilibrium checks pass; this does not mean that every updated damage state is fully equilibrated. All five material checks pass, with tensile-energy relative error below 0.00018%. The fresh default and strain-Rankine curves reproduce their previous saved curves exactly.

## Run and reconstruct

From the repository root, use a fresh workspace:

```powershell
python softwarex/run_equivalent_strain_study.py --workspace C:/runs/strain_study --stage all
```

Separate stages are `prepare`, `checks`, `solve` and `analyze`. The last
stage reads existing data and produces the plot; it does not run numerical
analyses. Current archived outputs are in
`reproducibility/equivalent_strain_study/`. Source/mesh hashes and explicit
criterion names are recorded in its plan and execution records.

```powershell
python softwarex/run_equivalent_strain_study.py --workspace softwarex/reproducibility/equivalent_strain_study --stage analyze --output C:/runs/strain_check
python softwarex/plot_current_figures.py --output C:/runs/current_figures
```

The analysis-only stage requires a separate output folder to preserve the archive.

## Sources

- [COMSOL Structural Mechanics Module, Damage Models, version 6.3](https://doc.comsol.com/6.3/doc/com.comsol.help.sme/sme_ug_theory.06.036.html), equivalent-strain definitions 3-81 through 3-86 and the distinction between a scalar driver and the complete Mazars model.
- J. H. P. de Vree, W. A. M. Brekelmans and M. A. J. van Gils, *Comparison of nonlocal approaches in continuum damage mechanics*, Computers & Structures 55(4), 581–588 (1995), [DOI](https://doi.org/10.1016/0045-7949(94)00501-S).
