# Validation scope

FRACMATH uses established damage and crack-band models. Its software contribution is a readable implementation with input files, numerical outputs and reproduction scripts.

- The 2D study includes two specimen sizes, three meshes and five computing configurations, with 90 timing observations. MATLAB assembly, factorization, damage and solve costs are measured separately. Abaqus sparse-solver costs and iteration counts are taken from job logs. A separate actual-UMAT timer records 2.996 s of raw call elapsed time with a 1.672 s clock-pair diagnostic. Native profiling identifies 2.873 s of assembly self estimates; full assembly wall time remains unavailable. These scopes are separate from the benchmark timing.
- Material-point checks compare MATLAB and the actual UMAT. The UMAT returns a degraded elastic secant matrix, so its equilibrium iterations differ from the MATLAB sequential scheme.
- The controlled 2D study compares Oliver and fixed-law load curves and partial dissipation on three identical exported meshes. Smaller-increment checks and energy/residual histories qualify the results.
- Figure 2 displays peak and final saved states with the same damage cutoff of 0.99. The final band reaches y=94.8 mm; the stricter 0.999999 cutoff reaches y=55.4 mm. Each panel states its cutoff and element count. These are computed damage bands, not measured open-crack lengths. No smoothing is used.
- The three-mesh 3D pure-tension plot compares the published specimen geometry with digitized measurements. The mixed-mode and torsion images are qualitative examples.

Figure 1 contains the 10,000-step MATLAB curve. Figures 4 and 5 use large shared colorbars. Figure 6 compares response curves; timing is shown separately in Figure 3.
