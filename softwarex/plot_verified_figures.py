"""Regenerate revised SoftwareX 2D figures from the corrected local runs."""

from pathlib import Path
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize, LinearSegmentedColormap
import numpy as np
from scipy.io import loadmat


HERE = Path(__file__).resolve().parent
OUT = HERE / "figures"
if (HERE / "reproducibility").exists():
    MAT10000 = HERE / "reproducibility/results_10000/verified_state.mat"
    ABQ = HERE / "reproducibility/abaqus/Gregoire_3PB/results/abaqus_load_cmod.csv"
    TIMING = HERE / "reproducibility/results_10000/matlab_timing.txt"
else:
    ROOT = HERE.parent
    MAT10000 = ROOT / "simulations/3pb_corrected/results_10000/verified_state.mat"
    ABQ = ROOT / "simulations/abaqus_corrected/Gregoire_3PB/results/abaqus_load_cmod.csv"
    TIMING = ROOT / "simulations/3pb_corrected/results_10000/matlab_timing.txt"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.labelsize": 11, "savefig.dpi": 240,
})
BLUE = "#205b88"
ORANGE = "#d1773f"


def state(path):
    return loadmat(path)


def save(fig, name):
    fig.savefig(OUT / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def mesh_figure(d):
    nodes = d["nodes"]
    elems = d["elems"].astype(int) - 1
    fig, ax = plt.subplots(figsize=(10.2, 4.0))
    ax.triplot(nodes[:, 0], nodes[:, 1], elems, color="#9eb0be", lw=.14)
    ax.set_xlim(-8, 358)
    ax.set_ylim(-19, 117)
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.annotate("applied displacement", (175, 100), (175, 115), ha="center",
                arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.8), color=ORANGE)
    ax.plot([50, 300], [-3, -3], "^", ms=8, color=BLUE, clip_on=False)
    ax.annotate("", (50, -10), (300, -10),
                arrowprops=dict(arrowstyle="<->", color=BLUE, lw=1.1))
    ax.text(175, -12.5, "support span 250 mm", ha="center", va="top",
            color=BLUE, fontsize=9, bbox=dict(facecolor="white", edgecolor="none", pad=1.0))
    ax.annotate("notch", (175, 9), (202, 26), ha="left",
                arrowprops=dict(arrowstyle="->", lw=1.0))
    save(fig, "fig_mesh_corrected.png")


def load_curve(d10):
    fig, ax = plt.subplots(figsize=(6.9, 4.4))
    x = d10["CMOD"].ravel()
    y = d10["F"].ravel() / 1000
    ax.plot(x, y, color=BLUE, lw=1.8, label="MATLAB, 10,000 fixed steps")
    i = np.argmax(y)
    ax.plot(x[i], y[i], "o", color=BLUE, ms=4)
    if ABQ.exists():
        rows = []
        with ABQ.open(newline="") as f:
            for row in csv.reader(f):
                try:
                    rows.append((float(row[0]), float(row[1])))
                except (ValueError, IndexError):
                    pass
        if rows:
            a = np.asarray(rows)
            ax.plot(a[:, 0], a[:, 1]/1000, color="#537c49", lw=1.5,
                    label="Abaqus UMAT, adaptive increments")
            j = np.argmax(a[:, 1])
            ax.plot(a[j, 0], a[j, 1]/1000, "o", color="#537c49", ms=4)
    ax.set(xlabel="CMOD (mm)", ylabel="reaction load (kN)")
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.grid(alpha=.2)
    ax.legend(frameon=False, loc="upper right")
    save(fig, "load_cmod_verified.png")


def damage_figure(d):
    nodes = d["nodes"]
    elems = d["elems"].astype(int) - 1
    panels = [(d["snap_peak"][0, 0], "At peak load"),
              (d["snap_pp"][0, 0], "Post peak, CMOD > 0.30 mm")]
    cmap = LinearSegmentedColormap.from_list(
        "damage_white_red", ["#f4f4f4", "#fff4cc", "#ffb06a", "#c9442d", "#711f22"])
    pd = ABQ.parent / "plotdata"
    has_abq = (pd / "omega_peak.csv").exists() and (pd / "omega_postpeak.csv").exists()
    fig, axes = plt.subplots(2, 2 if has_abq else 1,
                            figsize=(8.5 if has_abq else 5.2, 7.4), layout="constrained",
                            squeeze=False)
    abq_nodes = abq_elems = None
    if has_abq:
        abq_nodes = np.loadtxt(pd / "mesh_nodes.csv", delimiter=",", comments="#")[:, 1:3]
        abq_elems = np.loadtxt(pd / "mesh_elements.csv", delimiter=",", comments="#")[:, 1:4].astype(int) - 1
    for row, (snap, title) in enumerate(panels):
        omega = snap["omega"].ravel()
        coll = PolyCollection(nodes[elems], array=omega, cmap=cmap,
                              norm=Normalize(0, 1), edgecolors="none")
        ax = axes[row, 0]
        ax.add_collection(coll)
        ax.set_title("MATLAB: peak" if row == 0 else "MATLAB: postpeak",
                     loc="left", fontsize=10)
        if has_abq:
            fn = "omega_peak.csv" if row == 0 else "omega_postpeak.csv"
            values = np.loadtxt(pd / fn, delimiter=",", comments="#")
            abq_w = np.zeros(len(abq_elems))
            abq_w[values[:, 0].astype(int)-1] = values[:, 2]
            coll = PolyCollection(abq_nodes[abq_elems], array=abq_w, cmap=cmap,
                                  norm=Normalize(0, 1), edgecolors="none")
            ax = axes[row, 1]
            ax.add_collection(coll)
            ax.set_title("Abaqus: peak" if row == 0 else "Abaqus: postpeak",
                         loc="left", fontsize=10)
    for ax in axes.ravel():
        ax.set(xlim=(145, 205), ylim=(0, 100), xlabel="x (mm)", ylabel="y (mm)")
        ax.set_aspect("equal")
    fig.colorbar(coll, ax=axes, label="damage ω", shrink=.8, pad=.02)
    save(fig, "damage_verified.png")


def timing_figure():
    import re
    s = TIMING.read_text()
    labels = ["assembly", "factorization", "damage", "solve"]
    vals = [float(re.search(r"^  " + x + r":\s+([0-9.]+) s", s, re.M).group(1)) for x in labels]
    total = float(re.search(r"Solver wall-clock:\s+([0-9.]+)", s).group(1))
    labels.append("other")
    vals.append(max(0, total - sum(vals)))
    fig, ax = plt.subplots(figsize=(6.8, 3.4))
    bars = ax.barh(labels[::-1], vals[::-1], color=["#aeb9c3", "#6387a4", "#d79b70", ORANGE, BLUE][::-1])
    for bar, v in zip(bars, vals[::-1]):
        ax.text(v + total*.012, bar.get_y()+bar.get_height()/2,
                f"{v:.1f} s ({100*v/total:.1f}%)", va="center", fontsize=9)
    ax.set_xlim(0, max(vals)*1.28)
    ax.set_xlabel("wall clock (s)")
    ax.set_title("MATLAB 3PB, 10,000 steps, corrected code", loc="left")
    save(fig, "timing_verified.png")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    d10 = state(MAT10000)
    mesh_figure(d10)
    load_curve(d10)
    damage_figure(d10)
    timing_figure()
