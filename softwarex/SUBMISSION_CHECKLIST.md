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
| Software citation when a DOI/PID is supplied | Immutable source/data commit cited | Cite the tested release and its verified version-specific archive DOI |
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
- **3D published geometry:** the coarse pure-tension case has 35,917 TET4 elements
  and 21,828 DOFs. It completes 608 accepted increments with eight rejected trials,
  reaching 0.20 mm mean gauge displacement. Maximum accepted relative equilibrium
  residual is 8.917e-7. The simulated peak is 16.6415 kN versus digitized 19.8529 kN,
  a 16.18% underprediction; normalized curve RMS error is 9.27%.
- **Local 3D checks:** 32 tetrahedron size/direction cases, the compression mapping
  and eight rotating-direction damage-history cases pass. Projected width,
  tensile response, post-peak energy calibration and damage irreversibility are
  checked. These tests do not establish structural mesh convergence.

The manuscript describes these completed results and their limits. Figure 1
retains the preserved 10,000-step MATLAB response; Figures 4 and 5 retain the
large shared color bars. The illustrative 20 mm-notch geometry is distinct
from the quantitative published 25 mm-notch geometry.

## Remaining work for this submission

The separate Abaqus sampling collection and full beginner-entry execution are
complete. The profile identifies named assembly and user-library self estimates;
complete phase wall-time attribution remains unavailable. The entry exactly
reproduces every benchmark numerical state, response and snapshot array. Their
archives contain tested sources, paired-data checks and measurement scopes.

1. Finish and assess the medium/fine 3D pure-tension cases using the published
   25 mm notch geometry. The completed coarse case predicts 16.64 kN versus
   a digitized experimental peak of 19.85 kN (16.18% below). Explain this
   discrepancy and report only complete, converged histories. One mesh is
   insufficient for a 3D mesh-convergence claim.
2. Finish or explicitly delimit the strict proportional mixed-mode run. Its
   controls differ from the experimental 4a/4c sequence; do not add unmatched
   experimental overlays or use rejected/unconverged histories as validation.
3. Publish the final tested GitHub version, verify its automatic Zenodo archive,
   and add the correct software reference and metadata. The local citation
   metadata currently says `1.1.0-dev`; verify that the final manuscript's
   immutable source/data link contains every file supporting its results.
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
   `c65a73254d6aa62e5ea35c6e6852b875cab37f36`.

The three-mesh 3D study, GPU/SMP benchmarking and detailed Abaqus profiling
are evidence goals of this manuscript, not universal mandatory SoftwareX
tests. Claims must follow the completed evidence. The GPU implementation
has no measured speed advantage on this workstation; the software contribution
is inspectability, reproducible comparisons and regularization diagnostics.
