# SoftwareX submission checklist

Checked 3 October 2026 against Elsevier's original SoftwareX article
template, Version 6 (March 2026), retrieved again on this date.

- [Official article template](https://legacyfileshare.elsevier.com/promis_misc/softwarex-osp-template.docx)
- [Official reviewer form](https://legacyfileshare.elsevier.com/promis_misc/softwarex-reviewer-form.pdf)
- [Guide for authors](https://www.sciencedirect.com/journal/softwarex/publish/guide-for-authors)

The live Guide for Authors returned HTTP 403 during this check. Template
requirements and the reviewer form were accessible; submission-portal
requirements still need a final check.

## Manuscript and repository requirements

| Requirement | Current finding | Remaining action |
|---|---|---|
| Original software article template and five main sections | All five sections present | Preserve this structure in the final manuscript |
| Main text no more than 4,000 words | Automated count is recorded in `submission_checks.json`, excluding figures, tables, metadata and references | Recount after all final evidence is incorporated |
| Main text approximately six pages, excluding display material and references; word limit takes priority | Current evidence is incorporated into the manuscript source | Inspect the compiled body separately from total PDF pages |
| Abstract approximately 100 words | Describes 30 configurations with three observations each, totaling 90 runs | Retain approximately 100 words |
| Maximum six keywords | Six | Retain at most six |
| Maximum six figures | Six; the 3D comparison occupies an existing figure | Retain at most six |
| Metadata C1–C8, with template labels retained | Rows present | Pin C1/C2 to the final tested version and verify all links |
| Public GitHub repository with documented README.md and Licence.txt | Files present locally | Publish and verify the final source/data/docs on GitHub |
| Software citation when a DOI/PID is supplied | Release, immutable source and version DOI cited | Verified DOI 10.5281/zenodo.23138595 |
| Clear software architecture, functions, dependencies, examples and impact | Descriptions, examples and beginner guide present | Confirm the documented beginner workflow runs and supports the impact claims |

The reviewer form evaluates empirical evidence, readability, reproducibility,
documentation, dependencies, licensing and potential research impact. Passing
file checks does not predict editorial acceptance.

## Completed numerical evidence

- **Timing:** 30 size/mesh/computing configurations with three observations each,
  totaling 90 completed runs. Median times and observed ranges are archived.
  Saved MATLAB numerical arrays and Abaqus response CSVs match exactly between
  observations within each configuration; accepted-increment and solver-pass
  counts also match. MATLAB load-loop and Abaqus analysis/output times have
  different scopes.
- **2D regularization:** the controlled three-mesh family and smaller-increment
  checks are complete. At CMOD 0.10 mm, partial-dissipation spread is 6.86% with
  Oliver regularization versus 18.21% with the fixed law; at 4,000 increments,
  the spreads are 6.44% versus 20.76%. These measures qualify this mesh family,
  rather than establishing general mesh independence.
- **3D published geometry:** 35,917, 94,525 and 144,791 TET4 meshes
  complete their full 0.20 mm gauge paths within the 1e-6 equilibrium tolerance.
  Peak spread is 1.46%; medium/fine curve RMS difference is 0.35% of fine peak.
  Experimental peak underprediction remains 16.18–17.39%; curve NRMSE is
  9.09–9.27%. These errors remain explicit rather than removed by mesh choice.
- **Local 3D checks:** 32 tetrahedron size/direction cases, the compression mapping
  and eight rotating-direction damage-history cases pass. Projected width,
  tensile response, post-peak energy calibration and damage irreversibility are
  checked. These tests do not establish structural mesh convergence.

The 712-case UMAT audit, fresh energy tests and missing-gradient failure check pass. All eight generated manuscript assets reproduce with identical pixels; two supplied geometry illustrations match archived source bytes. The manuscript describes these completed results and their limits. Figure 1
retains the preserved 10,000-step MATLAB response; Figures 4 and 5 retain the
large shared color bars. The illustrative 20 mm-notch geometry is distinct
from the quantitative published 25 mm-notch geometry.

## Final submission checks

The separate Abaqus sampling collection and full beginner-entry execution are
complete. The profile identifies named assembly and user-library self estimates;
complete phase wall-time attribution remains unavailable. The entry exactly
reproduces every benchmark numerical state, response and snapshot array. Their
archives contain tested sources, paired-data checks and measurement scopes.

1. The three published-geometry 3D pure-tension meshes are complete. Their
   peaks are 16.64, 16.40 and 16.53 kN; peak spread is 1.46% and medium/fine
   curve RMS difference is 0.35% of fine peak. All histories pass the full
   equilibrium gate. Experimental underprediction remains 16.18–17.39%.
2. The strict proportional mixed-mode attempt stops at bisection exhaustion.
   Its failure record is preserved and explicitly delimited in the paper;
   it does not supply quantitative mixed-mode validation.
3. FRACMATH v1.1.1 is published at GitHub and automatically archived by
   Zenodo, DOI 10.5281/zenodo.23138595. The tag points to the source commit
   named in manuscript metadata and the software reference. All 366 archived
   file hashes match that tagged Git source, including raw run logs.
4. Review the contributions and affiliations/contact address. Jaykumar Mavani confirmed
   both-author submission approval, exclusive submission, the funding acknowledgement
   and no competing interests on 3 October 2026. Review the prepared `cover_letter.txt` and check the
   separate highlights and any portal-required declaration files. `author_confirmation.txt`
   lists the statements requiring author confirmation.
   The original cover letter cites v1.0.0 and a 3.6-fold MATLAB speed claim;
   it does not describe the present comparison. The original declaration
   discloses NASA/Space Grant financial support, while the paper declares no
   competing interests. Funding does not automatically imply a conflict;
   authors must confirm consistent wording across the submission files.
5. Repeat the PDF, file and delivery checks if further simulation results are
   incorporated. The manuscript names OpenAI Codex in its AI-use declaration
   and identifies the completed numerical evidence by immutable commit
   `f4d208ecf45b6a4e4d4530e5f71fbf8bcb9f0fe0`.

The three-mesh 3D study, GPU/SMP benchmarking and detailed Abaqus profiling
are evidence goals of this manuscript, not universal mandatory SoftwareX
tests. Claims must follow the completed evidence. The GPU implementation
has no measured speed advantage on this workstation; the software contribution
is inspectability, reproducible comparisons and regularization diagnostics.
