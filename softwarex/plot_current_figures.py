"""Build the current SoftwareX figures from archived numerical outputs.

Run with Python, NumPy, Matplotlib, SciPy and Pillow installed:
    python softwarex/plot_current_figures.py --output C:/runs/figures

No MATLAB or Abaqus analysis is started. Only completed fixed-increment
comparisons are shown in Figure 1. The failed fixed-increment cases remain
in the execution archive and its summary, without an adaptive replacement.
The native damage-update flowchart is supplied separately as editable TikZ.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np


PACKAGE = Path(__file__).resolve().parent
MODEL = "Gregoire_3PB"
BLUE = "#2166a5"
RED = "#cc503e"


def read_curve(path):
    values = np.loadtxt(path, delimiter=",", comments="#", ndmin=2)
    if values.shape[1] != 2 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("Invalid load-CMOD curve: " + str(path))
    return values


def checked_inputs(workspace):
    """Check the saved execution flags, actual schedules and mesh identities."""
    plan = json.loads((workspace / "plan.json").read_text(encoding="utf-8"))
    summary = json.loads((workspace / "analysis/summary.json").read_text(encoding="utf-8"))
    curves = {}
    for name in ("coarse", "medium", "fine"):
        settings = plan["cases"][name]
        result = summary["cases"][name]
        folder = workspace / name
        for filename, expected in settings["mesh_sha256"].items():
            path = folder / MODEL / "matlab_mesh" / filename
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError("Mesh differs from the execution plan: " + str(path))
        curves[name] = {}
        for mode, directory in (("oliver", "reference_matlab_oliver"),
                                ("area", "matlab_area")):
            if not result[mode]["passed_execution_checks"]:
                raise ValueError("Unverified MATLAB curve: " + name + "/" + mode)
            values = read_curve(folder / directory / "matlab_load_cmod.csv")
            if len(values) != settings["steps"]:
                raise ValueError("Incomplete MATLAB curve: " + name + "/" + mode)
            curves[name][mode] = values
        if name == "coarse":
            if not result["rankine"]["passed_execution_checks"]:
                raise ValueError("Unverified maximum-principal-strain comparison")
            values = read_curve(folder / "matlab_rankine/matlab_load_cmod.csv")
            if len(values) != settings["steps"]:
                raise ValueError("Incomplete maximum-principal-strain curve")
            curves[name]["rankine"] = values
        if name in ("medium", "fine"):
            if not result["abaqus"]["passed_execution_checks"]:
                raise ValueError("Fixed-increment Abaqus curve did not complete: " + name)
            if settings["steps"] != 2000 or settings["final_displacement_mm"] != -0.1:
                raise ValueError("Figure 1 requires the documented 2,000-step bending cases")
            schedule = np.genfromtxt(folder / MODEL / "results/abaqus_schedule.csv",
                                     delimiter=",", names=True)
            for field in schedule.dtype.names:
                if not np.isfinite(schedule[field]).all():
                    raise ValueError("Non-finite Abaqus history: " + name + "/" + field)
            if len(schedule) == settings["steps"] + 1 and abs(schedule["normalized_time"][0]) < 1.e-9:
                schedule = schedule[1:]
            times = np.arange(1, settings["steps"] + 1) / settings["steps"]
            if len(schedule) != settings["steps"] or not np.allclose(
                    schedule["normalized_time"], times, rtol=0, atol=1.e-7):
                raise ValueError("Actual Abaqus times differ from the fixed schedule: " + name)
            if not np.allclose(schedule["displacement_mm"],
                               settings["final_displacement_mm"] * times,
                               rtol=0, atol=2.e-8):
                raise ValueError("Actual Abaqus displacement differs from the fixed schedule: " + name)
            curves[name]["abaqus"] = np.column_stack((schedule["cmod_mm"], schedule["load_N"]))
    return plan, curves


def save(figure, folder, name, dpi=300):
    for suffix in ("png", "pdf"):
        figure.savefig(folder / (name + "." + suffix), dpi=dpi, facecolor="white")
    plt.close(figure)


def response_axes(axis):
    axis.set_xlabel("CMOD [mm]")
    axis.set_ylabel("Load [kN]")
    axis.grid(alpha=.2)
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_xlim(left=0)
    axis.set_ylim(bottom=0)


def figure_one(workspace, curves, output):
    mesh = workspace / "medium" / MODEL / "matlab_mesh"
    nodes = np.loadtxt(mesh / "nodes.txt", ndmin=2)
    elements = np.loadtxt(mesh / "elements.txt", dtype=int, ndmin=2)
    labels = {int(label): index for index, label in enumerate(nodes[:, 0])}
    triangles = np.array([[labels[int(label)] for label in row[1:]] for row in elements])
    coordinates = nodes[:, 1:3]
    edges = np.vstack((triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]))
    edges = np.unique(np.sort(edges, axis=1), axis=0)
    style = {"font.family": "DejaVu Sans", "font.size": 11,
             "axes.labelsize": 11, "axes.titlesize": 12,
             "axes.spines.top": False, "axes.spines.right": False}
    with plt.rc_context(style):
        figure = plt.figure(figsize=(10, 7.3), layout="constrained")
        grid = figure.add_gridspec(2, 2, height_ratios=(.95, 1.1))
        axis = figure.add_subplot(grid[0, :])
        axis.add_collection(LineCollection(coordinates[edges], colors="#9eb0be",
                                           linewidths=.17, rasterized=True))
        axis.set(xlim=(-7, 357), ylim=(-17, 113), xlabel="x [mm]", ylabel="y [mm]")
        axis.set_aspect("equal")
        axis.set_title("(a) Three-point bending: geometry and medium mesh", loc="left", fontweight="bold")
        axis.plot([50, 300], [0, 0], "^", color="#244660", markersize=10)
        axis.annotate("", xy=(50, -10), xytext=(300, -10),
                      arrowprops={"arrowstyle": "<->", "color": "#244660", "lw": 1.2})
        axis.text(175, -9, "250 mm support span", ha="center", va="bottom", fontsize=9)
        axis.annotate("Prescribed displacement", xy=(175, 100), xytext=(215, 109),
                      color="#b64231", fontsize=10,
                      arrowprops={"arrowstyle": "->", "color": "#b64231", "lw": 1.5})
        for column, (name, letter) in enumerate((("medium", "b"), ("fine", "c"))):
            axis = figure.add_subplot(grid[1, column])
            for mode, color, line, label in (("oliver", BLUE, "-", "MATLAB"),
                                            ("abaqus", RED, "--", "Abaqus/UMAT")):
                values = curves[name][mode]
                axis.plot(values[:, 0], values[:, 1] / 1000, line, color=color, linewidth=2, label=label)
                peak = int(np.argmax(values[:, 1]))
                axis.plot(values[peak, 0], values[peak, 1] / 1000, "o", color=color, markersize=5)
            response_axes(axis)
            axis.set_xlim(0, .15)
            axis.set_ylim(0, 4.8)
            axis.set_yticks(np.arange(5))
            axis.set_title("(%s) %s mesh" % (letter, name.capitalize()), loc="left", fontweight="bold")
            axis.text(.98, .95, "2,000 fixed increments\n" + r"$u_{final}=-0.1$ mm",
                      transform=axis.transAxes, ha="right", va="top", fontsize=10)
            axis.legend(frameon=False, loc="lower left", fontsize=10)
        save(figure, output, "figure1_fixed_advanced", dpi=220)


def formulation_figures(plan, curves, output):
    """Use the execution analyzer's plot sizes, labels and numerical data."""
    with plt.rc_context(plt.rcParamsDefault):
        figure, axes = plt.subplots(1, 3, figsize=(4.1 * 3, 3.6), squeeze=False)
        for axis, name in zip(axes.flat, ("coarse", "medium", "fine")):
            values = curves[name]
            axis.plot(values["oliver"][:, 0], values["oliver"][:, 1] / 1000,
                      color="#205b88", label="Oliver")
            axis.plot(values["area"][:, 0], values["area"][:, 1] / 1000, "--",
                      color="#ba543a", label=r"$h=\sqrt{2A}$")
            axis.set_title(name.capitalize())
            response_axes(axis)
            axis.legend(frameon=False)
        figure.tight_layout()
        save(figure, output, "area_versus_oliver")
        figure, axis = plt.subplots(figsize=(6.1, 4.0))
        values = curves["coarse"]
        axis.plot(values["oliver"][:, 0], values["oliver"][:, 1] / 1000,
                  color="#205b88", label="Modified von Mises")
        axis.plot(values["rankine"][:, 0], values["rankine"][:, 1] / 1000, "--",
                  color="#ba543a", label="Maximum positive principal strain")
        axis.set_title("Same coarse mesh, Oliver width and %d fixed increments" % plan["cases"]["coarse"]["steps"])
        response_axes(axis)
        axis.legend(frameon=False)
        figure.tight_layout()
        save(figure, output, "equivalent_strain_comparison")


def three_dimensional_figures(output):
    """Reuse the established 3D reconstruction functions and exact sources."""
    commands = [[sys.executable, str(PACKAGE / "rebuild_3d_figures.py"), "--output", str(output)]]
    with tempfile.TemporaryDirectory(prefix="fracmath_3d_figures_") as temporary:
        report = Path(temporary)
        commands.append([sys.executable, str(PACKAGE / "analyze_nooru_mesh_study.py"),
                         "--workspace", str(PACKAGE / "reproducibility/nooru_25mm_mesh_study"),
                         "--require-all", "--output", str(report)])
        for command in commands:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError("3D figure reconstruction failed:\n" + result.stdout + result.stderr)
        for suffix in ("png", "pdf"):
            shutil.copyfile(report / ("nooru_tension_mesh_comparison." + suffix),
                            output / ("nooru_tension_comparison." + suffix))
    for filename in ("nooru_BC_2D.png", "torsion.png"):
        shutil.copyfile(PACKAGE / "figure_sources/static" / filename, output / filename)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extension", type=Path, default=PACKAGE / "reproducibility/fixed_increment_extension")
    parser.add_argument("--output", type=Path, default=PACKAGE / "figures")
    parser.add_argument("--only-bending", action="store_true", help="Build only the three new bending figures")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    workspace = args.extension.resolve()
    plan, curves = checked_inputs(workspace)
    figure_one(workspace, curves, output)
    formulation_figures(plan, curves, output)
    if not args.only_bending:
        three_dimensional_figures(output)
    print("Current archive-backed figures saved in " + str(output))


if __name__ == "__main__":
    main()
