# Unified softening study

The pure-tension coarse, medium and fine TET4 runs completed with the same total-tensile-work convention as the three-point bending and torsion implementations: eps_f = kappa0/2 + GF/(h*ft). Their peaks are 16.635, 16.395 and 16.521 kN. The peak spread is 1.45%; the medium/fine difference relative to the fine peak is 0.76%.

The first fixed-target mixed-mode attempts failed to complete. The later opening-controlled continuation and its half-step check both reached the original proportional boundary endpoint without changing the material parameters or the 1e-6 equilibrium tolerance. The restart is the accepted 126-state prefix of the safeguarded attempt. The continuation required 183 additional accepted states; the half-step check required 384. See mixed_mode_solver_20261021/verification_summary.json and README.md for scope, commands, and checks.

Pure-tension verification is in analysis/summary.json. The current pure-tension plot is reconstructed from these histories. The earlier mixed-mode manuscript montage remains an earlier illustration until explicitly replaced; the completed new geometry and response comparison are supplied separately in mixed_mode_solver_20261021/analysis.

The supplied accepted restart, mesh, source, final states and response histories support reproduction. Large audit caches and per-step restart files are generated locally rather than versioned. The old local diagnostic attempts are preserved outside this published selection.
