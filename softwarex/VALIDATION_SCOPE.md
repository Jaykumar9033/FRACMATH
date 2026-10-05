# Validation and verification scope

FRACMATH implements established continuum-damage and crack-band concepts. The article validates the **software implementation and numerical consistency**, not a new constitutive theory.

## What is checked

- **Material point:** 712 deterministic prescribed material states are evaluated by MATLAB and the Abaqus UMAT. Equivalent strain, irreversible history, damage and stress are compared with permitted absolute difference `2e-10 + 2e-10 * abs(reference_value)`. This is not a one-element structural FEM test.
- **2D structure:** MATLAB and Abaqus solve the same notched three-point-bending benchmark. Load-CMOD curves and damage fields provide the cross-code structural comparison.
- **2D mesh sensitivity:** coarse, medium and fine meshes compare Oliver regularization with a fixed-width control. The manuscript discusses response curves, peak-load spread and increment sensitivity; dissipation is not a reported result.
- **3D pure tension:** three MATLAB/FRACMATH TET4 meshes provide a numerical mesh-consistency and equilibrium check. No experimental response curve is used.
- **3D mixed mode and torsion:** these panels are qualitative demonstrations. The torsion result shown in the manuscript is MATLAB/FRACMATH only; no Abaqus torsion solution is reported.
- **Performance:** timing records describe the tested hardware/software configurations only and are not a universal speed claim.

## What is not claimed

The package does not claim experimental validation of the 3D examples, universal mesh independence, a consistent damage tangent for the UMAT, or universal MATLAB/Abaqus/GPU speed superiority.

Separate UMAT instrumentation and native profiling supply partial timing diagnostics. Clock overhead, unidentified work and differing timer boundaries prevent complete material/assembly wall-time attribution. See [ABAQUS_TIMING_SCOPE.md](ABAQUS_TIMING_SCOPE.md).
