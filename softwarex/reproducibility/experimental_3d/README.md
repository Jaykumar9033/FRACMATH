# 3D experimental comparison

The numerical comparison uses Nooru-Mohamed specimen 47-05, pure tension with two glued platens, from Figure 3.16 (printed page 45) of the 1992 thesis. The CSV contains manually digitized estimates, not original machine records. Source details and pixel coordinates are in `experimental_source.json`. Reading uncertainty is approximately 0.00102 mm horizontally and 164 N vertically. The original thesis and its page images are not redistributed.

The nominal mesh contains 3,933 nodes and 18,927 TET4 elements. Existing material parameters are E=29,000 MPa, nu=0.2, ft=3 MPa, Gf=0.11 N/mm and compression/tension ratio 10; they are not fitted to this curve. Idealized top/bottom platen loading is controlled by the mean of four interpolated 65 mm vertical gauges at x=30/170 mm on the front/back faces. Gauge endpoint elements and interpolation weights accompany the data.

`source/damage_static.m` supports an optional gauge controller and constitutive numerical tangent for strict equilibrium. The controller solves for the common top-platen displacement together with free nodal displacements. Its constraint is the mean gauge displacement. The tangent differentiates the same damage update, including its directional crack-band width; unconverged increments raise an error. These options are selected explicitly by the runner.

Run `python softwarex/run_nooru_tension.py --workspace C:/runs/nooru_tension`, then `python softwarex/analyze_nooru_tension.py --workspace C:/runs/nooru_tension`. Licensed MATLAB and Python with numpy/matplotlib are required. Runs use one computational thread. The analysis requires all requested increments, finite values, equilibrium residual <=1e-6 and gauge constraint error <=1e-8 mm. Curve error is RMS on a uniform common displacement grid divided by experimental peak load. This is a single nominal-mesh comparison; it does not establish general 3D mesh independence.

The existing proportional mixed-mode and end-twist examples have different controls from the published experiments. Their damage images illustrate the workflow. The end-twist CMOD channel does not provide a valid experimental gauge measurement and is not used for a numerical experimental error claim.

An attempted 1,200-increment run failed equilibrium at increment 55 (relative residual 0.004185). Its incomplete history is excluded. This failure limits claims of load-increment convergence near peak localization.

The 300-increment attempt fails at increment 14 (relative residual 0.01430). Both failed runs are preserved in console logs and excluded from the comparison figure. The default runner reproduces the completed 600-increment case; `--steps 300 1200` reproduces the documented challenges.
