# Three completed published-geometry pure-tension meshes

All three meshes use the 200 x 200 x 50 mm panel, two 25 mm-deep and
5 mm-wide notches, unchanged material constants, idealized platens and
four interpolated 65 mm gauges. Mean gauge displacement controls the path
to 0.2 mm. Trial bisections reject unconverged damage updates.

| Mesh | TET4 elements | DOFs | Peak (kN) | Peak error (%) | Curve NRMSE (%) |
|---|---:|---:|---:|---:|---:|
| Coarse | 35,917 | 21,828 | 16.6415 | -16.18 | 9.27 |
| Medium | 94,525 | 54,540 | 16.3997 | -17.39 | 9.25 |
| Fine | 144,791 | 84,774 | 16.5261 | -16.76 | 9.09 |

All accepted relative equilibrium residuals meet 1e-6. Peak spread is
1.4636% of the three-peak mean; medium/fine curve RMS difference is 0.3467%
of fine peak. The remaining experimental discrepancy is much larger than
this mesh spread. These results concern one mesh family and do not prove
general mesh independence or increment convergence.

From the repository root, replay the full-history gate and regenerate Figure 3b:

```powershell
python softwarex/analyze_nooru_mesh_study.py --workspace softwarex/reproducibility/nooru_25mm_mesh_study --require-all
```

Copy a mesh subfolder to a separate workspace and execute `matlab -batch
run_case` there for a full structural rerun. Exact meshes, boundary sets,
gauge weights, generated solver, launcher, accepted targets, histories,
final state and console records are included. The three generated solvers
have identical tested hashes. The mesh builder uses Abaqus/CAE; rerunning
an archived mesh in MATLAB does not need a new Abaqus mesh build.

Experimental digitization and uncertainty are documented in
`../experimental_3d/experimental_source.json`. The separate 20 mm-notch
proportional damage images are qualitative and use different controls.

The original coarse-only package remains a record of that individual case.
Figure 3b in this manuscript uses all three curves from this study.
