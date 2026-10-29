# SoftwareX reproduction package

This folder contains study runners, reference results, figure sources and plotting scripts for the current FRACMATH manuscript. Start with `start_here.m`. [REPRODUCE.md](REPRODUCE.md) gives the full run sequence; record the exact repository commit.

## Guides

- [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md): first run, units, arrays and solver sequence.
- [NOTATION.md](NOTATION.md): manuscript symbols and code names.
- [COMPARISON_EXTENSION.md](COMPARISON_EXTENSION.md): matched three-point bending and width studies.
- [EQUIVALENT_STRAIN_STUDY.md](EQUIVALENT_STRAIN_STUDY.md): two equivalent-strain definitions.
- [SCALING_STUDY.md](SCALING_STUDY.md): five computing configurations and repeated timings.
- [UMAT_GUIDE.md](UMAT_GUIDE.md): material update and Abaqus connection.
- [ABAQUS_TIMING_SCOPE.md](ABAQUS_TIMING_SCOPE.md): what the timers measure.
- [VALIDATION_SCOPE.md](VALIDATION_SCOPE.md): supported conclusions and limitations.

## Reference records

The root [README](../README.md#reproduce-the-manuscript) maps results to their records. `reproducibility/2d` and `reproducibility/abaqus` supply executable sources and inputs. `mesh_study` supplies exact mesh resources. `fixed_increment_extension` and `fixed_increment_retry` retain completed comparisons and convergence diagnostics.

Current pure-tension records are in `reproducibility/unified_softening_20261014/mesh_study`. Completed mixed-mode continuation, the accepted restart, sources, final states and half-step checks are in `reproducibility/unified_softening_20261014/mixed_mode_solver_20261021`. Add `softwarex` to the MATLAB path and call `run_mixed_mode_continuation(workspace,true)` in a fresh writable workspace.

Earlier mixed-mode images in `figure_sources/nooru` and `reproducibility/nooru_proportional` use an earlier calibration. They remain qualitative illustrations, separate from the completed current calculation. Torsion fields are illustrative; Abaqus torsion files supply geometry and mesh resources.

`plot_current_figures.py` reconstructs response and damage figures; `verify_current_figures.py` checks them in a separate folder. The timing figure uses `plot_timing_repeats.py`; see `SCALING_STUDY.md`. Editable flowchart source is in `figure_sources/damage_update_flowchart.tex`.

Published beam-curve vertices and attribution are in `reproducibility/experimental_2d`. They are recovered graphic data, not raw laboratory measurements. No material fitting or experimental 3D validation is claimed.

Development-only profiles, larger UMAT audits and superseded replay studies have been removed. Source code and evidence used by the current manuscript remain available.
