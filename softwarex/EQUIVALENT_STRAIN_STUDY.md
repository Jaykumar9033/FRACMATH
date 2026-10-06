# Three equivalent-strain definitions

Figure 4 compares three scalar damage drivers in the MATLAB plane-stress
bending example. These are alternative equivalent-strain definitions used
inside the same FRACMATH history and exponential damage update, not complete
independently calibrated material models. The figure shows load versus CMOD
for modified von Mises, elastic energy and Rankine stress.

The figure also overlays the published experimental 100 mm beam trace from
Grassl et al. (2012), Figure 5, labelled `experiments 100 mm`. Its graphic
vertices are recovered from the native vector figure; they are not original
laboratory samples. Open markers select actual published graphic vertices,
not points generated from the numerical curves. The source record is in
[experimental_2d](reproducibility/experimental_2d/README.md).

## Definitions

Let `e1,e2,e3` be the elastic principal strains, including the recovered
plane-stress component `e3 = -nu/(1-nu)*(ex+ey)`. Define the undamaged
principal stresses by isotropic elasticity. Their dimensionless values are

`qi = sigma_i^0/E = ei/(1+nu) + nu*I1/((1+nu)*(1-2*nu))`,

where `I1 = e1+e2+e3`. Positive brackets mean `max(value,0)`.

| Setting | Figure label | Equivalent strain |
| --- | --- | --- |
| `modified_mises` | Modified von Mises | Existing de Vree invariant expression, using `I1`, `J2` and `k=fc/ft` |
| `elastic_energy` | Elastic energy | `sqrt(2*W0/E)`, where `W0 = 0.5*strain:C0:strain` |
| `rankine_stress` | Rankine (stress) | `max(q1,q2,q3,0)` |

The energy definition uses the total undamaged elastic energy and is normalized so that free uniaxial tension gives the axial strain. It is not a tensile-only energy split.

The two alternatives do not use `fc/ft`. Under free uniaxial
compression, the energy norm gives `abs(ex)` while Rankine stress gives zero.
All three reproduce the same equivalent strain
under free uniaxial tension. These differences must be considered when
choosing and calibrating a criterion for concrete.

## Controlled simulation settings

Every run uses the same exact coarse CPS3 mesh, 2,000 fixed increments,
final prescribed displacement -0.1 mm, CPU with one thread, Oliver width,
and the same E, nu, ft, GF and exponential softening calibration. Only the
equivalent-strain definition changes. The width formula remains identical;
its values can differ as the predicted strain direction changes.

The runner first checks ten material states with independent tensor
calculations for each criterion. It also checks tensile onset, four widths,
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
| Elastic energy | 1.346 | -67.91% |
| Rankine (stress) | 4.781 | +13.99% |

All three selected cases complete 2,000 increments and reach -0.1 mm prescribed displacement. Figure 4 retains load-CMOD points in loading order. Elastic energy reverses CMOD during later loading, so no single-valued common-CMOD RMS is reported for that path. No claim of experimental accuracy follows from these differences. A load-displacement panel is not included in the current figure.

The total-energy norm activates in compression with the same onset as free uniaxial tension; it is not calibrated to the input compressive strength. Its lower response illustrates sensitivity to that choice. Maximum post-damage relative residuals for the three selected cases range from 1.13% to 3.53%. Preceding-damage equilibrium checks pass, but fully equilibrated updated damage states are not claimed. Tensile-energy relative errors are below 0.00018%.

The total-energy normalization and implementation checks are recorded in `energy_normalization_audit.json`. The original five-run execution archive, including its other CPU options and formula audits, remains unchanged for traceability. Current figure reconstruction selects only the three responses above; this selection requires no new numerical run. The original Rankine-strain comparison remains under `reproducibility/equivalent_strain_study_20261006_rankine_strain/` for historical reproduction.

## Published experimental comparison

The selected short-notched beam has nominal depth 100 mm, thickness 50 mm,
support span 250 mm, length 350 mm and notch depth 20 mm. These dimensions
match the numerical example. The recovered trace peaks at 4.496 kN and
extends to CMOD 0.3363 mm. Figure 4 displays the common response region from
0 to 0.16 mm. The full recovered trace remains in the CSV.

The accessible author source does not establish the selected experimental
replicate identity, exact notch width or experimental loading control.
The trace must not be described as an identified individual test or
experimental mean. Not all numerical material inputs are verified measured
values for this test. No parameter fitting is performed. The overlay is a
comparison with published experimental evidence, not proof that the three
damage drivers have equally calibrated strength envelopes or equivalent
equilibrium accuracy.


## Run and reconstruct

From the repository root, use a fresh workspace:

```powershell
python softwarex/run_equivalent_strain_study.py --workspace C:/runs/strain_study --stage all
```

Separate stages are `prepare`, `checks`, `solve` and `analyze`. A fresh workspace
uses the three current definitions by default. The last
stage reads existing data and produces the plot; it does not run numerical
analyses. Current archived outputs are in
`reproducibility/equivalent_strain_study/`. Source/mesh hashes and explicit
criterion names are recorded in its plan and execution records.

```powershell
python softwarex/run_equivalent_strain_study.py --workspace softwarex/reproducibility/equivalent_strain_study --stage analyze --output C:/runs/strain_check
python softwarex/plot_current_figures.py --output C:/runs/current_figures
```

The analysis-only stage requires a separate output folder to preserve the archive. Analysis verifies the archived execution records; Figure 4 selects the three current load-CMOD histories. The earlier Rankine-strain comparison is a historical archive; it is not part of the current Figure 4 suite.

Default figure reconstruction also reads the experimental CSV and its
provenance. [extract_published_beam_curve.py](extract_published_beam_curve.py)
documents recovery from the author source, checks the native figure and
records its axis calibration. The original paper PDF is not redistributed
as software under the repository's MIT licence.

## Sources

- [COMSOL Structural Mechanics Module, Damage Models, version 6.3](https://doc.comsol.com/6.3/doc/com.comsol.help.sme/sme_ug_theory.06.036.html), energy and stress-based equivalent-strain definitions.
- J. H. P. de Vree, W. A. M. Brekelmans and M. A. J. van Gils, *Comparison of nonlocal approaches in continuum damage mechanics*, Computers & Structures 55(4), 581–588 (1995), [DOI](https://doi.org/10.1016/0045-7949(94)00501-S).
- P. Grassl, D. Grégoire, L. B. Rojas-Solano and G. Pijaudier-Cabot, *Meso-scale modelling of the size effect on the fracture process zone of concrete*, International Journal of Solids and Structures 49, 1818–1827 (2012), [DOI](https://doi.org/10.1016/j.ijsolstr.2012.03.023), [author source version](https://arxiv.org/abs/1107.2311v2), Figure 5.
