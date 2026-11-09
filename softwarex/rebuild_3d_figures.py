"""Compose archived 3D damage panels with one large, shared color bar.

The panel rasters are reused without changing their damage-field pixels.
Only layout, panel labels, and color bars are drawn here.
"""

from pathlib import Path
import argparse
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
SOURCES = HERE / "figure_sources"
OUT = HERE / "figures"
OUT.mkdir(exist_ok=True)
LETTERS = "abcdefghi"


def panel_label(ax, label):
    ax.text(.025, .97, label, transform=ax.transAxes, va="top", ha="left",
            fontsize=17, fontweight="bold", color="#111111",
            bbox=dict(facecolor="white", edgecolor="none", alpha=.85, pad=1.5))


def nooru():
    files = sorted((SOURCES / "nooru").glob("Job-1_inc_*.png"))
    assert len(files) == 9, f"Expected 9 Nooru panels, found {len(files)}"
    fig = plt.figure(figsize=(9.0, 7.8), dpi=300, facecolor="white")
    grid = fig.add_gridspec(3, 3, left=.012, right=.865, bottom=.018,
                            top=.982, wspace=.025, hspace=.025)
    for i, path in enumerate(files):
        ax = fig.add_subplot(grid[i//3, i%3])
        ax.imshow(Image.open(path).convert("RGB"), interpolation="nearest")
        ax.set_axis_off()
        inc = int(re.search(r"inc_(\d+)", path.name).group(1))
        panel_label(ax, f"({LETTERS[i]}) {inc}")
    cax = fig.add_axes([.90, .09, .034, .82])
    sm = plt.cm.ScalarMappable(norm=colors.Normalize(.95, 1.0), cmap="turbo")
    cb = fig.colorbar(sm, cax=cax, ticks=[.95,.96,.97,.98,.99,1.0])
    cb.ax.set_yticklabels(["0.95","0.96","0.97","0.98","0.99","1.00"])
    cb.ax.tick_params(labelsize=13, length=6, width=1)
    cb.set_label(r"Damage $\omega$", fontsize=16, labelpad=14)
    fig.savefig(OUT / "nooru_damage_evolution_shared_bar.png", dpi=300,
                facecolor="white")
    plt.close(fig)


def torsion():
    import subprocess
    import sys
    subprocess.run([sys.executable, str(SOURCES / "plot_torsion_evolution.py"),
                    "--output", str(OUT)], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT)
    OUT = parser.parse_args().output
    OUT.mkdir(parents=True, exist_ok=True)
    nooru()
    torsion()
    print("Saved Nooru-Mohamed and torsion damage montages")
