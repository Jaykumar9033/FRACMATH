# Manuscript evidence map

| Claim or scope | Evidence | Interpretation |
|---|---|---|
| 824 local material cases agree | `reproducibility/umat_precision/history/summary.json` | Independent tensor reference and actual MATLAB damage functions; local scope |
| Unloading/reloading and rotation checks | `reproducibility/umat_precision/history/history_checks.json` | 112 states on 16 paths; irreversible histories and symmetric nonnegative secant stiffness |
| UMAT batch measurement | `reproducibility/umat_precision/summary.json` | Ten batches in two fresh processes; driver cost included; no structural extrapolation |
| Seven in-job UMAT blocks | `reproducibility/abaqus_phase_timing/blocks/block_timing_summary.json` | Raw intrusive timings, dominated by clock effects; no precise block percentages |
| Abaqus solver and total analysis timing | `reproducibility/abaqus/Gregoire_3PB/diagnostics/Gregoire_3PB.msg` | Unallocated remainder is not identified assembly/material time |
| Thirty matched computing configurations, 90 observations | `reproducibility/timing_repeats/analysis/summary.json` | All recorded repeat-response checks pass; algorithms and timing scopes differ |
| Mesh-family load curves and partial dissipation | `reproducibility/mesh_study/summary.json` | Completed response comparison; no complete mesh-independence claim |
| Three-mesh pure-tension comparison | `reproducibility/nooru_25mm_mesh_study/analysis/summary.json` | Published geometry, digitized experiment and measured mismatch disclosed |
| Peak/final damage bands | `plot_verified_figures.py` and 2D archives | Same 0.99 cutoff; not measured fully open cracks |
| Mixed-mode and torsion fields | Archived figure sources and validation scope | Qualitative illustrations |
| Current manuscript figures | `verify_paper_figures.py` | Seven generated assets and two supplied illustrations across five numbered figures |
| Core version and DOI | `software_release.json` and DataCite metadata | Existing v1.1.1 archive; additional evidence uses a separate immutable companion commit |

The material tangent is the documented degraded elastic secant matrix, not a consistent derivative during evolving damage. The manuscript retains this numerical limit. The batch microbenchmark improves timing interval precision without claiming complete Abaqus phase allocation.

References were checked for internal citation completeness and DOI metadata. Crossref records verify four journal references; publisher pages verify the two rate-limited journal records. DataCite verifies the existing software DOI. The existing thesis/manual/toolbox references are retained with their archived source context. These checks are not a guarantee that every reference URL is continuously accessible.
