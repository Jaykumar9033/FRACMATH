# Validation evidence and scope

| Reviewer concern | Implementation and evidence | Remaining boundary |
| --- | --- | --- |
| Established constitutive model has no new model novelty | Frame the contribution as inspectable software for SoftwareX; keep the model summary concise and show the code map and load-step algorithm | No new constitutive model; GPU backend scope and measured limits are stated |
| Benchmark too small | Controlled regularization family plus a two-size/three-mesh/five-configuration hardware study, up to 100,104 T3 elements and 101,088 DOFs; exact paired meshes and completed jobs supplied | One 2D geometry family; workstation observations with no industrial-scale performance claim |
| Solver cost mislabeled as assembly | Separate MATLAB assembly, factorization, damage, and solve scopes; report actual component times | Timers are one-run observations |
| Abaqus timing incomplete | Parse every sparse-solver timer from completed `.msg`, verify pass counts, and report accepted increments, cutbacks, decompositions, wall time, and unallocated remainder | `.msg` does not separately measure UMAT, assembly, convergence, or output; no attribution of the remainder or speed ranking |
| Possible UMAT or solver usage error | Use the same pairwise J2 definition in both 2D codes; supply matched source, exact mesh input, completed-job logs, and code-to-code response checks | Close responses alone do not prove a bug-free UMAT; sequential MATLAB and Abaqus equilibrium algorithms differ |
| Too little implementation detail | Function map, load-step sequence, projected-width implementation, state history, and per-step diagnostics | One nominal-mesh 3D pure-tension comparison is quantitative; mixed-mode/torsion examples remain qualitative |
| Insufficient regularization evidence | MATLAB/UMAT material-point energy calibration, explicit unload/reload checks, and 16 rotated-strain UMAT checks; structural Oliver-versus-fixed-law control across three meshes; dissipation at common CMOD, energy balance, and smaller-increment checks | Tests assess one geometry/path; no general mesh or orientation independence claim |

The controlled mesh study and the single-mesh 1,000/10,000-step
example use separate protocols. Figure 1 retains only the 10,000-step MATLAB curve
and Abaqus response. Figures 4 and 5 retain their large shared color bars.
Figure 6 presents the controlled study. Numerical conclusions are taken from
`reproducibility/mesh_study/summary.json`, not estimated timings.

## Experimental 3D comparison and Abaqus profiling scope

A nominal-mesh pure-tension test uses published specimen 47-05 data digitized from Nooru-Mohamed's thesis. Four 65 mm local gauges control the simulation; The 600-increment simulation completes. Attempts at 300 and 1,200 increments fail near peak localization; increment convergence is not established. Parameters are retained without fitting. Peak and curve errors, data-reading uncertainty, and boundary idealizations are reported. Mixed-mode and end-twist pictures remain qualitative.

The final Abaqus `.dat` CPU totals accompany the existing elapsed and solver timers. Separate material/assembly timing could not be established: per-call UMAT timers dominate short calls, and Windows denied CPU profiling privileges. The elapsed remainder is not assigned to either phase.

An attempted 1,200-increment run failed equilibrium at increment 55 (relative residual 0.004185). Its incomplete history is excluded. This failure limits claims of load-increment convergence near peak localization.

The 300-increment attempt fails at increment 14 (relative residual 0.01430). Both failed runs are preserved in console logs and excluded from the comparison figure. The default runner reproduces the completed 600-increment case; `--steps 300 1200` reproduces the documented challenges.

## CPU, hybrid GPU and SMP size/mesh study

All 30 configurations complete and pass the declared within-program hardware-response checks. The same mesh files are used within every comparison; archived decks, states, histories, timers and failed default-control localization attempt preserve the evidence. GPU kernels, transfers, CPU sparse factorization, eight-thread MATLAB library limits, and eager Abaqus SMP table initialization are explained in the code walkthrough. MATLAB factorization occupies 67-74% of CPU1 loop time. The hybrid GPU is slower on all six tested cases; larger Abaqus cases benefit from SMP. See [SCALING_STUDY.md](SCALING_STUDY.md). Separate Abaqus material/assembly profiling and general 3D mesh independence remain outside the established evidence.
