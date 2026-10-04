# Validation scope

FRACMATH uses established damage and crack-band models. Its software contribution is a readable implementation with input files, numerical outputs and reproduction scripts.

- The 2D study includes two specimen sizes, three meshes and five computing configurations, with 90 timing observations. MATLAB assembly, factorization, damage and solve costs are measured separately. Abaqus sparse-solver costs and iteration counts are taken from job logs. A separate actual-UMAT timer records 2.996 s of raw call elapsed time with a 1.672 s clock-pair diagnostic. Native profiling identifies 2.873 s of assembly self estimates; full assembly wall time remains unavailable. These scopes are separate from the benchmark timing.
- Material-point checks compare MATLAB and the actual UMAT. The UMAT returns a degraded elastic secant matrix, so its equilibrium iterations differ from the MATLAB sequential scheme.
- The controlled 2D study compares Oliver and fixed-law load curves and partial dissipation on three identical exported meshes. Smaller-increment checks and energy/residual histories qualify the results.
- Figure 2 displays peak and final saved states with the same damage cutoff of 0.99. The final band reaches y=94.8 mm; the stricter 0.999999 cutoff reaches y=55.4 mm. Each panel states its cutoff and element count. These are computed damage bands, not measured open-crack lengths. No smoothing is used.
- The three-mesh 3D pure-tension plot shows numerical curves for the published specimen geometry. Digitized measurements are retained in the archive and textual comparison, without experimental points in the figure. The mixed-mode and torsion images are qualitative examples.

Figure 1 contains the 10,000-step MATLAB curve. Figures 3 and 4 use large shared colorbars. Figure 5 compares completed response curves. Timing is reported in tables.

The [evidence map](CLAIM_EVIDENCE.md) links manuscript claims to completed datasets. The [UMAT precision archive](reproducibility/umat_precision/README.md) supplies 824 local cases, ten external batches and an independently executed fresh-process replay. These measurements do not provide full Abaqus assembly wall time.
