"""Plot the two reaction channels in the illustrative proportional history.

This is a diagnostic history, not an equilibrium-verified experimental test.
Run from the repository root: python softwarex/plot_nooru_proportional.py
"""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    package = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path, default=package/"reproducibility/nooru_proportional")
    parser.add_argument("--output", type=Path, default=package/"figures")
    args = parser.parse_args()
    source = args.case/"response_history.csv"
    parameters = json.loads((args.case/"case_description.json").read_text())
    if hashlib.sha256(source.read_bytes()).hexdigest() != parameters["history_sha256"]:
        raise ValueError("History hash differs from the archived record")
    history = np.genfromtxt(source, delimiter=",", names=True, usecols=(0, 1, 2, 3, 11))
    fields = ("delta_s_mm", "delta_mm", "Ps_N", "P_N", "relative_residual")
    if len(history) != 900 or not all(np.isfinite(history[name]).all() for name in fields):
        raise ValueError("Require the complete finite 900-row diagnostic history")
    if (not np.allclose(history["delta_s_mm"], .6*history["delta_mm"])
            or not np.isclose(history["delta_mm"][-1], .5)
            or np.any(np.diff(history["delta_mm"]) <= 0)):
        raise ValueError("History does not match the proportional displacement path")
    passed = history["relative_residual"] <= 1e-6
    failed = np.flatnonzero(~passed)
    # Crosses identify sampled failed increments; the CSV retains every residual.
    marked = np.unique(np.r_[failed[::10], failed[-1], np.argmax(history["P_N"])])
    marked = marked[~passed[marked]]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), layout="constrained")
    for ax, xname, yname, xlabel, ylabel, title in (
        (axes[0], "delta_s_mm", "Ps_N", r"Shear displacement $\delta_s$ (mm)",
         r"Shear reaction magnitude $P_s$ (kN)", "(a) Shear response"),
        (axes[1], "delta_mm", "P_N", r"Top displacement $\delta$ (mm)",
         r"Normal reaction $P$ (kN)", "(b) Normal response")):
        x, y = history[xname], history[yname]/1000
        ax.plot(np.r_[0, x], np.r_[0, y], color="#526b80", lw=1.4, label="Recorded response")
        ax.scatter(x[marked], y[marked], marker="x", color="#c13e36", s=18, linewidths=.8,
                   label=r"Residual $>10^{-6}$ (sampled)")
        ax.scatter(x[passed], y[passed], color="#26734d", s=15,
                   label=r"Residual $\leq10^{-6}$")
        ax.set(xlabel=xlabel, ylabel=ylabel, title=title, xlim=(0, x[-1]))
        ax.axhline(0, color="#777777", lw=.6)
        ax.grid(alpha=.18)
        ax.legend(frameon=False, fontsize=8, loc="best")
    fig.suptitle("Proportional loading: 20 mm notches, shear/tension displacement ratio 0.6", fontsize=12)
    args.output.mkdir(parents=True, exist_ok=True)
    for extension in ("pdf", "png"):
        fig.savefig(args.output/("nooru_proportional_responses."+extension), dpi=300)
    plt.close(fig)
    summary = {
        "history_sha256": parameters["history_sha256"],
        "recorded_increments": len(history), "equilibrium_tolerance": 1e-6,
        "increments_above_tolerance": int((~passed).sum()),
        "maximum_relative_residual": float(history["relative_residual"].max()),
        "final_relative_residual": float(history["relative_residual"][-1]),
        "interpretation": "Diagnostic only; no experimental validation or converged response claim.",
        "normal_recorded_peak_kN": float(history["P_N"].max()/1000),
        "shear_recorded_maximum_kN": float(history["Ps_N"].max()/1000),
    }
    (args.case/"summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
