"""Compose archived 3D damage panels with one large, shared color bar.

The panel rasters are reused without changing their damage-field pixels.
Only layout, panel labels, and color bars are drawn here.
"""

from pathlib import Path
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
    files = sorted((SOURCES / "torsion").glob("Job-1_StaticFast_mod_vm_LIVE_snap_inc_*.png"))
    assert len(files) == 8, f"Expected 8 torsion panels, found {len(files)}"
    # Sample the original MATLAB color bar to retain its exact display palette.
    key = np.asarray(Image.open(files[0]).convert("RGB"))
    sampled = key[20:780, 1090, :][::-1]
    cmap = colors.ListedColormap(sampled[np.linspace(0, len(sampled)-1, 256).astype(int)] / 255)
    fig = plt.figure(figsize=(9.0, 6.65), dpi=300, facecolor="white")
    grid = fig.add_gridspec(3, 3, left=.01, right=.865, bottom=.025,
                            top=.975, wspace=.025, hspace=.045)
    for i, path in enumerate(files):
        ax = fig.add_subplot(grid[i//3, i%3])
        source = Image.open(path).convert("RGB")
        ax.imshow(source.crop((42, 68, 1045, 782)), interpolation="nearest")
        ax.set_axis_off()
        inc = int(re.search(r"inc_(\d+)", path.name).group(1))
        panel_label(ax, f"({LETTERS[i]}) {inc}")
    cax = fig.add_axes([.90, .095, .034, .81])
    sm = plt.cm.ScalarMappable(norm=colors.Normalize(0, 1), cmap=cmap)
    cb = fig.colorbar(sm, cax=cax, ticks=[0,.2,.4,.6,.8,1.0])
    cb.ax.tick_params(labelsize=13, length=6, width=1)
    cb.set_label(r"Damage $\omega$", fontsize=16, labelpad=14)
    fig.savefig(OUT / "torsion_damage_evolution_shared_bar.png", dpi=300,
                facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    nooru()
    torsion()
    print("Saved revised Nooru-Mohamed and torsion damage montages")
