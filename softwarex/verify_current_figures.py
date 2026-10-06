"""Rebuild and compare the current manuscript's numerical figure assets.

PNG pixels are compared exactly. PDF pages are rendered with pdftoppm and
compared by pixels, allowing PDF creation dates to differ. Removed adaptive
response figures are outside this check. The editable TikZ flowchart is a
separate source artifact; its compilation can be checked in a LaTeX editor.

Example:
    python softwarex/verify_current_figures.py --workspace C:/runs/figure_check
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image


PACKAGE = Path(__file__).resolve().parent
GENERATED = (
    "figure1_fixed_advanced.png", "figure1_fixed_advanced.pdf",
    "area_versus_oliver.png", "area_versus_oliver.pdf",
    "equivalent_strain_comparison.png", "equivalent_strain_comparison.pdf",
    "nooru_tension_comparison.png", "nooru_tension_comparison.pdf",
    "nooru_damage_evolution_shared_bar.png", "torsion_damage_evolution_shared_bar.png",
)
STATIC = ("nooru_BC_2D.png", "torsion.png")


def pixels(path):
    with Image.open(path) as picture:
        return np.asarray(picture.convert("RGBA"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--figures", type=Path, default=PACKAGE / "figures")
    parser.add_argument("--extension", type=Path, default=PACKAGE / "reproducibility/fixed_increment_extension")
    parser.add_argument("--pdftoppm", default="pdftoppm", help="Program name or absolute Poppler executable path")
    args = parser.parse_args()
    folder = args.workspace.resolve()
    if folder.exists() and any(folder.iterdir()):
        raise SystemExit("Use an empty workspace to preserve earlier verification results")
    folder.mkdir(parents=True, exist_ok=True)
    program = shutil.which(args.pdftoppm)
    if program is None:
        raise SystemExit("pdftoppm was not found; supply --pdftoppm with its executable path")
    rebuilt = folder / "rebuilt"
    command = [sys.executable, str(PACKAGE / "plot_current_figures.py"),
               "--extension", str(args.extension.resolve()), "--output", str(rebuilt)]
    with (folder / "reconstruction.log").open("w", encoding="utf-8") as stream:
        subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True)
    checks = []
    for filename in GENERATED:
        original = args.figures.resolve() / filename
        regenerated = rebuilt / filename
        if original.suffix == ".pdf":
            rendered = []
            for label, source in (("original", original), ("rebuilt", regenerated)):
                prefix = folder / (original.stem + "_" + label)
                subprocess.run([program, "-singlefile", "-r", "100", "-png",
                                str(source), str(prefix)], check=True, capture_output=True)
                rendered.append(prefix.with_suffix(".png"))
            original, regenerated = rendered
        left, right = pixels(original), pixels(regenerated)
        same_shape = left.shape == right.shape
        checks.append({"asset": filename, "identical_pixels": bool(same_shape and np.array_equal(left, right)),
                       "shape_matches": same_shape})
    for filename in STATIC:
        original = args.figures.resolve() / filename
        source = PACKAGE / "figure_sources/static" / filename
        checks.append({"asset": filename, "identical_archived_source_bytes":
                       hashlib.sha256(original.read_bytes()).digest() == hashlib.sha256(source.read_bytes()).digest(),
                       "scope": "Supplied geometry illustration, not a numerical response plot."})
    flowchart = PACKAGE / "figure_sources/damage_update_flowchart.tex"
    source = flowchart.read_text(encoding="utf-8")
    if r"\begin{tikzpicture}" not in source or r"\end{tikzpicture}" not in source:
        raise ValueError("Native damage-update TikZ source is missing its figure environment")
    passed = all(item.get("identical_pixels", item.get("identical_archived_source_bytes")) for item in checks)
    report = {"passed": passed, "assets": checks,
              "scope": "Current archived-data figure reproduction; numerical solver validation and native TikZ compilation are separate checks.",
              "removed_adaptive_figures_checked": False,
              "native_flowchart": {"source": "softwarex/figure_sources/damage_update_flowchart.tex",
                                   "sha256": hashlib.sha256(flowchart.read_bytes()).hexdigest(),
                                   "scope": "Editable TikZ source identity recorded; compile separately in LaTeX."}}
    (folder / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit("A current figure differs from its archived-data reconstruction")


if __name__ == "__main__":
    main()
