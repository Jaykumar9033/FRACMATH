"""Draw the 2D front view of the actual mixed-mode mesh and prescribed boundaries.

Geometry and grip memberships come from the completed mixed-mode model.
Only the front projection is drawn; no 3D view is exported.
"""
from pathlib import Path
import argparse
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.lines import Line2D
import numpy as np
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MESH = ROOT / "reproducibility/unified_softening_20261014/mixed_mode_solver_20261021"
COLORS = {"top": "#d62728", "bottom": "#1f77b4",
          "left": "#2ca02c", "right": "#9467bd"}


def load_mesh(folder):
    table = np.loadtxt(folder / "Job-1_nodes.txt")
    elements = np.loadtxt(folder / "Job-1_elements.txt").astype(int)
    points = table[:, 1:4]
    lookup = {int(label): row for row, label in enumerate(table[:, 0])}
    tet = np.array([[lookup[int(i)] for i in row[1:5]] for row in elements])
    faces = np.vstack([tet[:, idx] for idx in
                       ([0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3])])
    faces, counts = np.unique(np.sort(faces, axis=1), axis=0, return_counts=True)
    surface = faces[counts == 1]
    sets = {}
    for name in COLORS:
        labels = np.loadtxt(folder / ("Job-1_" + name + "_nodes.txt")).astype(int)
        sets[name] = np.array([lookup[int(i)] for i in labels.ravel()])
    return points, tet, surface, sets


def arrow2(ax, start, end, color):
    ax.annotate("", xy=end, xytext=start,
                arrowprops=dict(arrowstyle="-|>", mutation_scale=16,
                                lw=1.5, color=color))


def front_view(ax, p, surface, sets):
    front = surface[np.all(np.isclose(p[surface, 2], 0), axis=1)]
    ax.add_collection(PolyCollection(p[front, :2], facecolors="#f2f2f5",
                                    edgecolors="#92929d", linewidths=.32))
    edges = np.vstack([front[:, [0, 1]], front[:, [0, 2]], front[:, [1, 2]]])
    edges, counts = np.unique(np.sort(edges, axis=1), axis=0, return_counts=True)
    edges = edges[counts == 1]
    for a, b in edges:
        xy = p[[a, b], :2]
        ax.plot(xy[:, 0], xy[:, 1], color="#50505b", lw=1.2)
    for name, ids in sets.items():
        mask = np.isin(edges[:, 0], ids) & np.isin(edges[:, 1], ids)
        for edge in edges[mask]:
            xy = p[edge, :2]
            ax.plot(xy[:, 0], xy[:, 1], color=COLORS[name], lw=3.2,
                    solid_capstyle="butt")
    for x in np.linspace(10, 190, 6):
        arrow2(ax, (x, 95), (x, 124), COLORS["top"])
    for y in np.linspace(4, 79, 5):
        arrow2(ax, (-35, y), (-3, y), COLORS["left"])
    for y in np.linspace(-99, -24, 5):
        arrow2(ax, (234, y), (203, y), COLORS["right"])
    # Rollers indicate a vertical restraint, not a full bottom clamp.
    for x in np.linspace(15, 185, 6):
        ax.plot([x], [-115], marker="^", markersize=7,
                markerfacecolor="white", markeredgecolor=COLORS["bottom"],
                markeredgewidth=1.4)
        ax.plot([x-2, x+2], [-122, -122], linestyle="none", marker="o",
                markersize=2, markerfacecolor="white",
                markeredgecolor=COLORS["bottom"], markeredgewidth=.8)
        ax.plot([x-5, x+5], [-126, -126], color=COLORS["bottom"], lw=1.2)
    ax.text(100, 134, r"$u_y=+0.50$ mm", color=COLORS["top"],
            ha="center", fontsize=16, weight="normal")
    ax.text(-47, 42, r"$u_x=+0.15$ mm", color=COLORS["left"],
            ha="center", va="center", rotation=90, fontsize=15)
    ax.text(247, -63, r"$u_x=-0.15$ mm", color=COLORS["right"],
            ha="center", va="center", rotation=90, fontsize=15)
    ax.text(100, -140, r"$u_y=0$", color=COLORS["bottom"],
            ha="center", va="top", fontsize=16, weight="normal")
    for label, tip, text in [("Left notch", (10, -10), (47, 27)),
                              ("Right notch", (190, -10), (108, -47))]:
        ax.annotate(label, xy=tip, xytext=text, fontsize=12.5,
                    bbox=dict(facecolor="white", edgecolor="none", pad=1),
                    arrowprops=dict(arrowstyle="->", color="#333333", lw=.9))
    ax.set(xlim=(-62, 263), ylim=(-168, 153), xlabel="x (mm)", ylabel="y (mm)")
    ax.xaxis.label.set_fontweight("normal")
    ax.yaxis.label.set_fontweight("normal")
    ax.set_aspect("equal")
    ax.set_xticks([0, 50, 100, 150, 200])
    ax.set_yticks([-100, -50, 0, 50, 100])
    ax.tick_params(labelsize=13, width=1)
    ax.set_title("Boundary conditions (front view)", fontsize=16, weight="bold", pad=13)
    return front


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mesh", type=Path, default=DEFAULT_MESH)
    parser.add_argument("--output", type=Path, default=ROOT / "figures")
    args = parser.parse_args()
    p, tet, surface, sets = load_mesh(args.mesh)
    assert np.allclose(p.min(axis=0), [0, -110, 0])
    assert np.allclose(p.max(axis=0), [200, 90, 50])
    assert np.allclose(p[sets["left"]].min(axis=0), [0, -7.5, 0])
    assert np.allclose(p[sets["right"]].max(axis=0), [200, -12.5, 50])
    volumes = np.abs(np.linalg.det(
        p[tet[:, 1:]] - p[tet[:, 0, None]])) / 6
    assert np.isclose(volumes.sum(), 1990000)
    # Check the drawn displacements against both completed solver states.
    state_checks = {}
    for case in ["continuation_full", "continuation_refined"]:
        state = loadmat(args.mesh / case / "final_state.mat", simplify_cells=True)
        displacement = state["U"].reshape(-1, 3)
        checks = {}
        for name, component, target in [
                ("top", 1, .5), ("bottom", 1, 0),
                ("left", 0, .15), ("right", 0, -.15)]:
            values = displacement[sets[name], component]
            error = float(np.max(np.abs(values - target)))
            assert error < 1e-12, (case, name, "Boundary displacement differs")
            checks[name] = {"component": "xyz"[component], "target_mm": target,
                            "maximum_error_mm": error}
        pin = np.argmin(p[:, 2])
        assert abs(displacement[pin, 2]) < 1e-12
        checks["z_pin"] = {"row_index": int(pin), "xyz_mm": p[pin].tolist(),
                           "uz_mm": float(displacement[pin, 2])}
        state_checks[case] = checks
    args.output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 16,
                         "axes.labelsize": 16, "axes.linewidth": 1})
    fig = plt.figure(figsize=(5.8, 5.8), facecolor="white")
    ax = fig.add_axes([.14, .09, .76, .82])
    front_view(ax, p, surface, sets)
    pin = np.argmin(p[:, 2])
    ax.plot(p[pin, 0], p[pin, 1], marker="D", color="black",
            markersize=4.5, linestyle="none", zorder=5)
    pin_key = Line2D([0], [0], color="black", marker="D", linestyle="none",
                     markersize=4.5, label=r"$u_z=0$")
    ax.legend(handles=[pin_key], loc="upper left", frameon=False,
              fontsize=11.5, handlelength=.8, borderaxespad=.5)
    for suffix in ["png", "pdf"]:
        fig.savefig(args.output / ("nooru_boundary_conditions." + suffix),
                    dpi=450, bbox_inches="tight", pad_inches=.08)
    plt.close(fig)
    report = {"view": "2D front projection only", "mesh_folder": str(args.mesh), "nodes": len(p), "tetrahedra": len(tet),
              "dimensions_mm": [200, 200, 50], "notch_depth_mm": 20,
              "notch_width_mm": 5, "mesh_volume_mm3": float(volumes.sum()),
              "top_final_uy_mm": .5, "upper_left_final_ux_mm": .15,
              "lower_right_final_ux_mm": -.15, "bottom_uy_mm": 0,
              "out_of_plane_restraint": "u_z=0 at the first node with minimum z; black diamond",
              "saved_final_state_checks": state_checks,
              "loading": "Proportional prescribed displacements, not applied forces.",
              "node_sets": {name: {"nodes": len(ids),
                  "min_xyz": p[ids].min(axis=0).tolist(),
                  "max_xyz": p[ids].max(axis=0).tolist()} for name, ids in sets.items()},
              "mesh_sha256": {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                  for f in sorted(args.mesh.glob("Job-1_*nodes.txt"))}}
    (args.output / "nooru_boundary_conditions_verification.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
