# Validation evidence and scope

| Reviewer concern | Implementation and evidence | Remaining boundary |
| --- | --- | --- |
| Established constitutive model has no new model novelty | Frame the contribution as inspectable software for SoftwareX; keep the model summary concise and show the code map and load-step algorithm | No new constitutive model; GPU backend scope and measured limits are stated |
| Benchmark too small | Controlled regularization family plus a two-size/three-mesh/five-configuration hardware study, up to 100,104 T3 elements and 101,088 DOFs; exact paired meshes and completed jobs supplied | One 2D geometry family; workstation observations with no industrial-scale performance claim |
| Solver cost mislabeled as assembly | Separate MATLAB assembly, factorization, damage, and solve scopes; report actual component times | Hardware timings have three observations per configuration; other protocols retain their declared scopes |
| Abaqus timing incomplete | Parse every sparse-solver timer from completed `.msg`, verify pass counts, and report accepted increments, cutbacks, decompositions, wall time, and unallocated remainder | `.msg` does not separately measure UMAT, assembly, convergence, or output; no attribution of the remainder or speed ranking |
| Possible UMAT or solver usage error | Use the same pairwise J2 definition in both 2D codes; supply matched source, exact mesh input, completed-job logs, and code-to-code response checks | Close responses alone do not prove a bug-free UMAT; sequential MATLAB and Abaqus equilibrium algorithms differ |
| Too little implementation detail | Function map, load-step sequence, projected-width implementation, state history, and per-step diagnostics | One geometry-matched 3D pure-tension comparison is quantitative; mixed-mode/torsion examples remain qualitative |
| Insufficient regularization evidence | MATLAB/UMAT material-point energy calibration, explicit unload/reload checks, and 16 rotated-strain UMAT checks; structural Oliver-versus-fixed-law control across three meshes; dissipation at common CMOD, energy balance, and smaller-increment checks | Tests assess one geometry/path; no general mesh or orientation independence claim |

The controlled mesh study and the single-mesh 1,000/10,000-step
example use separate protocols. Figure 1 retains only the 10,000-step MATLAB curve
and Abaqus response. Figures 4 and 5 retain their large shared color bars.
Figure 6 presents coarse/medium/fine response overlays for both programs,
with peak and dissipation comparisons. Timing appears separately in Figure 3.
Numerical conclusions are taken from
`reproducibility/mesh_study/summary.json`, not estimated timings.

## Experimental 3D comparison and Abaqus profiling scope

The separate proportional mixed-mode response archive contains two panels:
shear reaction magnitude versus side displacement and signed normal reaction
versus top displacement. Its recorded residual exceeds 1e-6 at 894 of 900
increments. The figure marks these points and remains a diagnostic outside
the main paper; it does not supply mixed-mode experimental validation.
The internal `4c` option uses simultaneous proportional displacement control,
which differs from the published experimental loading sequence.

The quantitative pure-tension case uses published specimen 47-05 dimensions with 25 mm notches, 35,917 TET4 elements and four interpolated 65 mm gauges. The 600 initial intervals produce 608 accepted increments with eight rejected/bisected trials. The peak is 16.64 kN versus the digitized experimental 19.85 kN (16.18% below); curve NRMSE is 9.27%. All accepted equilibrium residuals are below 1e-6. Source-linked local checks cover 32 size/direction cases, compression mapping and eight rotating-direction unloading/history cases. Parameters are retained without fitting. The completed three-mesh family has 1.46% peak spread and 0.35% medium/fine curve RMS difference; general mesh independence and increment convergence are not established. The separate 20 mm-notch histories and mixed-mode/torsion pictures are idealized or qualitative evidence.

The Abaqus `.dat` CPU totals accompany elapsed and sparse-solver timers. A complete separate software-sampling profile has exactly matching mesh/boundary hashes and 2,001 response rows. VTune self estimates are 2.03 s in the user-subroutine library and 3.81 s in four explicitly named assembly routines. Self samples exclude callees and incomplete symbols; they do not establish complete material/assembly wall times or allocate the benchmark's remainder. Raw function/call-stack exports, warnings and scope limits are archived in `reproducibility/abaqus_profile/`.

## CPU, hybrid GPU and SMP size/mesh study

All 30 configurations have three complete observations (90 runs) and pass the declared within-program hardware-response checks. The same mesh files are used within every comparison; archived decks, states, histories, timers and failed default-control localization attempt preserve the evidence. GPU kernels, transfers, CPU sparse factorization, eight-thread MATLAB library limits, and eager Abaqus SMP table initialization are explained in the code walkthrough. MATLAB factorization occupies 67-76% of CPU1 loop time. The hybrid GPU is slower on all six tested cases; larger Abaqus cases benefit from SMP. See [SCALING_STUDY.md](SCALING_STUDY.md). Complete Abaqus material/assembly wall-time attribution and general 3D mesh independence remain outside the established evidence.

The actual 10,000-step beginner entry, with graphics disabled alone, exactly
reproduces all eight geometry/state/response arrays and six peak/post-peak
snapshot arrays or values. Tested code, mesh, complete output and comparison
manifest are in `reproducibility/beginner_entry_check/`. This execution is a
numerical reproduction check and does not enter the timing study.


## UMAT and manuscript figure checks

See [UMAT_GUIDE.md](UMAT_GUIDE.md) for the constitutive sequence and secant-tangent limitation. The actual UMAT passes 712 independent material-point comparisons and comparisons with the MATLAB damage functions. Fresh energy/unloading tests and the missing-gradient failure check pass. The tested sources and outputs are archived in `reproducibility/umat_audit/`.

The complete three-mesh 25 mm-notch study is archived in `reproducibility/nooru_25mm_mesh_study/`. All histories reach 0.2 mm gauge displacement within the equilibrium tolerance. Peak underprediction remains 16.18–17.39%; the mesh spread does not explain the experimental discrepancy. The strict mixed-mode failure is preserved in `reproducibility/nooru_proportional_strict/`.

Run `python softwarex/verify_paper_figures.py --workspace C:/runs/figure_replay` from the repository root to rebuild the manuscript figures in a separate folder. All eight generated assets pass pixel comparison; two supplied geometry illustrations match their archived sources. Runtime and PDF metadata are not numerical reproduction targets.
