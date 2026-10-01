# Validation evidence and scope

| Reviewer concern | Implementation and evidence | Remaining boundary |
| --- | --- | --- |
| Established constitutive model has no new model novelty | Frame the contribution as inspectable software for SoftwareX; keep the model summary concise and show the code map and load-step algorithm | No new constitutive model or GPU claim |
| Benchmark too small | Controlled mesh family: 14,313 / 25,042 / 56,216 T3 elements, with exact supports and fixed loading strip; MATLAB and Abaqus job records supplied | One 2D family; no multithreaded or industrial-scale performance claim |
| Solver cost mislabeled as assembly | Separate MATLAB assembly, factorization, damage, and solve scopes; report actual component times | Timers are one-run observations |
| Abaqus timing incomplete | Parse every sparse-solver timer from completed `.msg`, verify pass counts, and report accepted increments, cutbacks, decompositions, wall time, and unallocated remainder | `.msg` does not separately measure UMAT, assembly, convergence, or output; no attribution of the remainder or speed ranking |
| Possible UMAT or solver usage error | Use the same pairwise J2 definition in both 2D codes; supply matched source, exact mesh input, completed-job logs, and code-to-code response checks | Close responses alone do not prove a bug-free UMAT; sequential MATLAB and Abaqus equilibrium algorithms differ |
| Too little implementation detail | Function map, load-step sequence, projected-width implementation, state history, and per-step diagnostics | 3D examples remain qualitative |
| Insufficient regularization evidence | MATLAB/UMAT material-point energy calibration, explicit unload/reload checks, and 16 rotated-strain UMAT checks; structural Oliver-versus-fixed-law control across three meshes; dissipation at common CMOD, energy balance, and smaller-increment checks | Tests assess one geometry/path; no general mesh or orientation independence claim |

The controlled mesh study and the single-mesh 1,000/10,000-step
example use separate protocols. Figure 1 retains only the 10,000-step MATLAB curve
and Abaqus response. Figures 4 and 5 retain their large shared color bars.
Figure 6 presents the controlled study. Numerical conclusions are taken from
`reproducibility/mesh_study/summary.json`, not estimated timings.
