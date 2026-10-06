# Published experimental load–CMOD trace

Figure 4 uses the series labelled **experiments 100 mm** in Figure 5 of
Grassl, Grégoire, Rojas Solano and Pijaudier-Cabot, *Meso-scale modelling of
the size effect on the fracture process zone of concrete*, IJSS 49 (2012),
1818–1827, [DOI](https://doi.org/10.1016/j.ijsolstr.2012.03.023).
The [author manuscript](https://arxiv.org/pdf/1107.2311v2) reports the
Grégoire experimental campaign.

Nominal dimensions match the current beam: depth 100 mm, thickness 50 mm,
span 250 mm, length 350 mm and notch depth 20 mm. The experimental notch
width and original control details are not verified in this accessible
source. FRACMATH uses a 2.5 mm notch and prescribed load-point displacement.
Its material inputs have not been fitted to this digitized curve.

The CSV contains 3,206 **published graphic vertices**, not 3,206 laboratory
samples. These form one continuous trace; the source does not identify it
as a particular replicate or a mean. Original coordinates, axis calibration,
source hashes, extraction method and limits are recorded in `provenance.json`.
The published peak is approximately 4.50 kN at CMOD 0.0291 mm. Graphic
quantization is not measurement uncertainty, and no experimental confidence
interval is inferred.

Figure 4 shows the 0–0.16 mm CMOD window covering the numerical responses.
Open circles mark a subset of actual graphic vertices; no points are generated
from simulated curves. The complete digitized trace extends to 0.3363 mm.
The source's model curves and numerical error bars are excluded.

## Reproduce digitization

Download the [versioned author source bundle](https://arxiv.org/src/1107.2311v2)
to a separate folder. With NumPy and pypdf installed, run from the repository root:

```powershell
python softwarex/extract_published_beam_curve.py --bundle C:/sources/1107.2311v2.tar.gz --output C:/runs/beam_digitization
```

This recovers the selected native vector path and verifies the CSV checksum.
No laboratory measurement is reconstructed beyond the published graphic.
The original PDF, source bundle and image are not redistributed here.
The arXiv distribution licence is not a software licence; source authorship
and its data limitations remain applicable to these attributed numerical facts.
