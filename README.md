# FRACMATH

FRACMATH is a vectorized MATLAB finite-element implementation of scalar continuum damage with direction-dependent Oliver crack-band regularization. The current repository accompanies a **SoftwareX manuscript in preparation** by Jaykumar Mavani and Madura Pathirage (University of New Mexico). It presents an inspectable implementation of established methods, not a new constitutive model.

## Start here

| Item | Location | Purpose |
| --- | --- | --- |
| Corrected 2D MATLAB solver | [`3pb/matlab/solver_main_3pb.m`](3pb/matlab/solver_main_3pb.m) | Notched three-point bending; `FRACMATH_STEPS`, `FRACMATH_HEADLESS`, and `FRACMATH_SELFTEST` controls |
| Corrected Abaqus UMAT and job builder | [`3pb/abaqus/`](https://github.com/Jaykumar9033/FRACMATH/tree/main/3pb/abaqus) | Matched material update and Oliver T3 gradient table; use one CPU |
| SoftwareX manuscript and figures | [`softwarex/`](https://github.com/Jaykumar9033/FRACMATH/tree/main/softwarex) | Draft PDF, TeX, figure sources, plotting scripts, and verified data |
| Reproduction instructions | [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) | Commands, environment, checks, and numerical limitations |
| 3D examples | [`Noor mohammad/`](https://github.com/Jaykumar9033/FRACMATH/tree/main/Noor%20mohammad), [`Torsion/`](https://github.com/Jaykumar9033/FRACMATH/tree/main/Torsion) | Archived qualitative examples; not rerun for this revision |
| Theory manual | [`doc/theory_manual.tex`](doc/theory_manual.tex) | Equations and corrected solver explanation; PDF pending recompilation |

The 2D invariant implementation was corrected to
`J2 = ((e1-e2)^2 + (e2-e3)^2 + (e3-e1)^2)/6` in both MATLAB and the Abaqus UMAT. The previous public [`v1.0.0`](https://github.com/Jaykumar9033/FRACMATH/tree/v1.0.0) tag and [Zenodo record](https://doi.org/10.5281/zenodo.21297071) document the earlier AES-era version and **do not reproduce the current SoftwareX 2D figures**. A new versioned SoftwareX release and DOI have not yet been published.

## Verified 2D results

The preserved fixed-step MATLAB runs used 1,000 and 10,000 displacement steps. Their peak loads are 4.26464 and 4.02633 kN, respectively. The corrected one-CPU Abaqus run reached 3.99914 kN with 1,136 accepted adaptive increments and 4,817 solver passes. Its 832 s wall time includes more than the 100.2 s summed sparse-solver timer. The distinct step histories and unknown time spent in UMAT, assembly, convergence, and output do not support a speed-ranking claim. These results are for one mesh; structural mesh objectivity has not been demonstrated.

The material-point test checks tensile/compressive equivalent strain, damage irreversibility, Oliver width, and fracture-energy calibration for widths of 0.5, 1, 2, and 4 mm. The 3D panels in the manuscript use archived AES images with improved color bars and labels. Their underlying simulations were not rerun in this revision.

## Run

Use MATLAB R2024b or a compatible release for the 2D script. From `3pb/matlab`, run `solver_main_3pb`. Set `FRACMATH_HEADLESS=1` to omit live figures and video; set `FRACMATH_STEPS=1000` or `10000` to select the run length. Set `FRACMATH_SELFTEST=1` to run the material-point check.

From `3pb/abaqus`, run `abaqus cae noGUI=run_3pb_abaqus_OLIVER_T3_FAST.py` with Abaqus/Standard 2024 and a configured Intel Fortran compiler. Set `ABQ_CPUS=1`: the current UMAT table reader has not been made thread-safe for multiple Abaqus workers.

From `softwarex`, run `python plot_verified_figures.py` to regenerate the 2D manuscript figures from the preserved result files. Run `python rebuild_aes_figures.py` to recompose the archived 3D panels with shared color bars. Install Python dependencies with `python -m pip install -r requirements.txt` from the repository root. See the [full guide](REPRODUCIBILITY.md) for commands and expected outputs.

## Citation and license

This repository is MIT licensed. [`CITATION.cff`](CITATION.cff) describes the current development code without assigning it the historical `v1.0.0` DOI. Cite a new release DOI once the SoftwareX version is tagged and archived.
