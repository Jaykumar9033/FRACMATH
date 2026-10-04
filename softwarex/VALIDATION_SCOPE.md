# Validation scope

FRACMATH uses established damage and crack-band models. Its software contribution is a readable implementation with input files, numerical outputs and reproduction scripts.

- The 2D study includes two specimen sizes, three meshes and five computing configurations, with 90 timing observations. MATLAB assembly, factorization, damage and solve costs are measured separately. Abaqus sparse-solver costs and iteration counts are taken from job logs. Complete Abaqus material and assembly wall times are not available.
- Material-point checks compare MATLAB and the actual UMAT. The UMAT returns a degraded elastic secant matrix, so its equilibrium iterations differ from the MATLAB sequential scheme.
- The controlled 2D study compares Oliver and fixed-law load curves and partial dissipation on three identical exported meshes. Smaller-increment checks and energy/residual histories qualify the results.
- Figure 2 displays severe damage at peak (damage at least 0.99) and fully damaged elements after peak (damage at least 0.999999). Each panel states its cutoff and element count. These are computed damage bands, not measured open-crack lengths. No smoothing is used.
- The three-mesh 3D pure-tension plot compares the published specimen geometry with digitized measurements. The mixed-mode and torsion images are qualitative examples.

Figure 1 contains the 10,000-step MATLAB curve. Figures 4 and 5 use large shared colorbars. Figure 6 compares response curves; timing is shown separately in Figure 3.
