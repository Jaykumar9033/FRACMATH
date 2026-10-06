# Theory manual

This folder contains the theory manual for the FRACMATH formulation and solver
implementation used by the SoftwareX manuscript.

## Files

| File | Purpose |
| --- | --- |
| `theory_manual.tex` | LaTeX source |
| `theory_manual.pdf` | Generated locally when compiling the source; not committed until the PDF is verified |

## What the manual covers

- Scalar isotropic continuum damage mechanics.
- Modified von Mises equivalent strain.
- Exponential softening.
- Crack-band regularization.
- Direction-dependent Oliver bandwidth.
- Consistent tangent concept and the implemented sequential secant update.
- Notes connecting the MATLAB and Abaqus/UMAT implementations.

## Rebuild command

From this folder, run:

```bash
pdflatex theory_manual.tex
pdflatex theory_manual.tex
```

A complete LaTeX distribution is required to rebuild the PDF.

The manual describes the default Oliver/modified-von-Mises formulation.
The current CPU area-width and principal-strain alternatives, fixed-increment
comparisons and their verification limits are documented in
[`softwarex/COMPARISON_EXTENSION.md`](../softwarex/COMPARISON_EXTENSION.md).
The editable calculation diagram is in
[`softwarex/figure_sources/damage_update_flowchart.tex`](../softwarex/figure_sources/damage_update_flowchart.tex).
