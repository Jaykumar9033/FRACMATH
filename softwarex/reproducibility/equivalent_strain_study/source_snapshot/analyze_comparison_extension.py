"""Check the fixed-increment/regularization extension and plot complete cases.

python softwarex/analyze_comparison_extension.py --workspace C:/runs/extension

Execution checks establish schedules, exact meshes and finite recorded outputs.
They do not establish experimental validation or identical nonlinear algorithms.
Failed fixed-increment Abaqus jobs remain visible in summary.json and are not
plotted as completed solutions. Existing Oliver curves retain their provenance.
"""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import re

import numpy as np
from scipy.io import loadmat
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from run_comparison_extension import MODEL, validate_frozen_inputs, save_json


def curve(path):
    values = np.loadtxt(path, delimiter=",", comments="#", ndmin=2)
    if values.shape[1] != 2 or not np.isfinite(values).all() or len(values) < 2:
        raise ValueError("Invalid response: " + str(path))
    return values


def matlab_check(folder, mesh, settings, regularization, equivalent_strain):
    values = curve(folder / "matlab_load_cmod.csv")
    state = loadmat(folder / "verified_state.mat", simplify_cells=True)
    parameters = state["p"]
    if parameters["num_steps"] != settings["steps"] or len(values) != settings["steps"]:
        raise ValueError("MATLAB did not complete the specified number of increments")
    if abs(parameters["max_disp"] - settings["final_displacement_mm"]) > 1.e-12:
        raise ValueError("MATLAB final displacement setting differs")
    if parameters["regularization"] != regularization:
        raise ValueError("MATLAB regularization setting differs")
    if parameters.get("equivalent_strain", "modified_mises") != equivalent_strain:
        raise ValueError("MATLAB equivalent-strain setting differs")
    for key in ("nodes", "elems", "u", "omega", "kappa", "CMOD", "F", "RelRes"):
        if not np.isfinite(state[key]).all():
            raise ValueError("Non-finite MATLAB state: " + key)
    if np.min(state["omega"]) < -1.e-12 or np.max(state["omega"]) > 1 + 1.e-12:
        raise ValueError("MATLAB damage is outside [0,1]")
    nodes = np.loadtxt(mesh / "nodes.txt", ndmin=2)
    elements = np.loadtxt(mesh / "elements.txt", dtype=int, ndmin=2)
    mapping = {int(label): index for index, label in enumerate(nodes[:, 0])}
    expected_elements = np.array([[mapping[int(label)] + 1 for label in row[1:]] for row in elements])
    if not np.allclose(state["nodes"], nodes[:, 1:3], rtol=0, atol=2.e-12):
        raise ValueError("MATLAB coordinates differ from the exact job mesh")
    if not np.array_equal(state["elems"], expected_elements):
        raise ValueError("MATLAB connectivity differs from the exact job mesh")
    top = np.atleast_1d(np.loadtxt(mesh / "top_nodes.txt", dtype=int))
    top_indices = np.array([mapping[int(label)] * 2 + 1 for label in top])
    if not np.allclose(np.ravel(state["u"])[top_indices], settings["final_displacement_mm"], rtol=0, atol=1.e-12):
        raise ValueError("MATLAB saved state did not reach the final prescribed displacement")
    diagnostics = np.genfromtxt(folder / "matlab_step_diagnostics.csv", delimiter=",", names=True)
    if len(diagnostics) != settings["steps"]:
        raise ValueError("Missing MATLAB per-step diagnostics")
    for field in diagnostics.dtype.names:
        if not np.isfinite(diagnostics[field]).all():
            raise ValueError("Non-finite MATLAB diagnostic: " + field)
    if not np.array_equal(diagnostics["step"], np.arange(1, settings["steps"] + 1)):
        raise ValueError("MATLAB diagnostic step sequence differs")
    if not np.all(diagnostics["old_damage_converged"] == 1):
        raise ValueError("A MATLAB old-damage linear equilibrium solve failed")
    history = np.genfromtxt(folder / "matlab_energy_history.csv", delimiter=",", names=True)
    expected_displacement = -settings["final_displacement_mm"] * np.arange(1, settings["steps"] + 1) / settings["steps"]
    if len(history) != settings["steps"] or not np.allclose(history["displacement_mm"], expected_displacement, rtol=0, atol=1.e-10):
        raise ValueError("MATLAB saved displacement history differs from the fixed schedule")
    peak = int(np.argmax(values[:, 1]))
    result = {"passed_execution_checks": True, "steps": len(values),
        "peak_load_N": float(values[peak, 1]), "peak_cmod_mm": float(values[peak, 0]),
        "final_cmod_mm": float(values[-1, 0]),
        "maximum_post_damage_relative_residual": float(np.max(diagnostics["post_damage_relative_residual"])),
        "peak_post_damage_relative_residual": float(diagnostics["post_damage_relative_residual"][peak]),
        "regularization": regularization, "equivalent_strain": equivalent_strain,
        "interpretation": "Old-damage equilibrium passes; post-damage residual is reported separately."}
    if regularization == "area":
        triangles = nodes[expected_elements - 1, 1:3]
        a, b = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
        widths = np.sqrt(np.abs(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]))
        if not np.isfinite(widths).all() or np.min(widths) <= 0:
            raise ValueError("Invalid element area")
        expected_width = np.array([np.mean(widths), np.min(widths), np.max(widths)])
        saved = np.loadtxt(folder / "matlab_oliver_bandwidth_history.csv", delimiter=",", comments="#", ndmin=2)
        if len(saved) != settings["steps"] or not np.allclose(saved[:, 1:4], expected_width, rtol=2.e-6, atol=1.e-8):
            raise ValueError("Saved widths differ from sqrt(2*A)")
        result["area_width_mean_min_max_mm"] = expected_width.tolist()
    return result, values


def printed_tolerance(token):
    """The .sta time fields are rounded; allow half the last printed unit."""
    return 0.5001 * 10.0 ** Decimal(token).as_tuple().exponent + 1.e-12


def abaqus_check(job, settings):
    text = (job / (MODEL + ".sta")).read_text()
    if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" not in text:
        raise ValueError("Fixed-increment Abaqus job did not complete")
    input_text = (job / (MODEL + ".inp")).read_text()
    keyword = re.search(r"(?im)^\*static[^\r\n]*", input_text)
    if keyword is None or "direct" not in keyword.group().lower() or "no stop" in keyword.group().lower():
        raise ValueError("Expected DIRECT with NO STOP disabled")
    rows = []
    for line in text.splitlines():
        tokens = line.split()
        if len(tokens) < 9 or not all(token.isdigit() for token in tokens[:6]):
            continue
        rows.append(tokens)
    n = settings["steps"]
    if len(rows) != n or [int(row[1]) for row in rows] != list(range(1, n + 1)):
        raise ValueError("Abaqus .sta does not contain the requested complete increment sequence")
    for index, row in enumerate(rows, 1):
        if int(row[0]) != 1 or int(row[2]) != 1:
            raise ValueError("Unexpected step or repeated increment attempt in .sta")
        for token, expected in ((row[7], index / n), (row[8], 1 / n)):
            if abs(float(token) - expected) > printed_tolerance(token):
                raise ValueError("Abaqus .sta schedule differs at increment %d" % index)
    schedule = np.genfromtxt(job / "results/abaqus_schedule.csv", delimiter=",", names=True)
    for field in schedule.dtype.names:
        if not np.isfinite(schedule[field]).all():
            raise ValueError("Non-finite Abaqus history: " + field)
    # ODB histories can store single-precision time/displacement values. The
    # tolerances below resolve every 1/10000 increment while allowing that storage.
    time = schedule["normalized_time"]
    if len(time) == n + 1 and abs(time[0]) < 1.e-9:
        schedule = schedule[1:]
        time = schedule["normalized_time"]
    expected_time = np.arange(1, n + 1) / n
    if len(time) != n or not np.allclose(time, expected_time, rtol=0, atol=1.e-7):
        raise ValueError("Actual ODB history times differ from the fixed schedule")
    target = settings["final_displacement_mm"] * expected_time
    tolerance = max(1.e-8, abs(settings["final_displacement_mm"]) * 2.e-7)
    if not np.allclose(schedule["displacement_mm"], target, rtol=0, atol=tolerance):
        raise ValueError("Actual Abaqus displacement differs from the MATLAB schedule")
    values = np.column_stack([schedule["cmod_mm"], schedule["load_N"]])
    peak = int(np.argmax(values[:, 1]))
    return {"passed_execution_checks": True, "fixed_increments": n,
        "maximum_history_time_error": float(np.max(np.abs(time - expected_time))),
        "maximum_displacement_error_mm": float(np.max(np.abs(schedule["displacement_mm"] - target))),
        "final_displacement_mm": float(schedule["displacement_mm"][-1]),
        "final_cmod_mm": float(values[-1, 0]), "peak_load_N": float(values[peak, 1]),
        "peak_cmod_mm": float(values[peak, 0]), "adaptive_increments": False,
        "no_stop": False, "time_tolerance": 1.e-7, "displacement_tolerance_mm": tolerance}, values


def comparison(reference, other):
    peak_a, peak_b = float(np.max(reference[:, 1])), float(np.max(other[:, 1]))
    result = {"reference_peak_N": peak_a, "comparison_peak_N": peak_b,
        "peak_difference_percent": 100 * (peak_b - peak_a) / peak_a}
    if np.any(np.diff(reference[:, 0]) < -1.e-8) or np.any(np.diff(other[:, 0]) < -1.e-8):
        result["curve_rms_status"] = "CMOD reversal requires explicit branch comparison"
        return result
    lower = max(float(reference[0, 0]), float(other[0, 0]))
    upper = min(float(reference[-1, 0]), float(other[-1, 0]))
    if upper <= lower:
        result["curve_rms_status"] = "No common CMOD interval"
        return result
    grid = np.linspace(lower, upper, 2001)
    difference = np.interp(grid, other[:, 0], other[:, 1]) - np.interp(grid, reference[:, 0], reference[:, 1])
    result.update(common_cmod_range_mm=[lower, upper], curve_rms_N=float(np.sqrt(np.mean(difference**2))),
                  curve_rms_percent_reference_peak=float(100 * np.sqrt(np.mean(difference**2)) / peak_a))
    return result


def axes_style(axis):
    axis.set_xlabel("CMOD [mm]")
    axis.set_ylabel("Load [kN]")
    axis.grid(alpha=.2)
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_xlim(left=0)
    axis.set_ylim(bottom=0)


def save_figure(figure, folder, name):
    figure.tight_layout()
    figure.savefig(folder / (name + ".png"), dpi=300)
    figure.savefig(folder / (name + ".pdf"))
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    plan = json.loads((workspace / "plan.json").read_text())
    output = workspace / "analysis"
    output.mkdir(exist_ok=True)
    summary = {"execution_checks_complete": False, "physical_validation_claim": False,
        "source_sha256": plan["source_sha256"], "cases": {}, "errors": [],
        "limitations": plan["limitations"],
        "comparison_policy": "Same exact mesh, fixed increment count and displacement endpoint; different nonlinear algorithms."}
    try:
        validate_frozen_inputs(workspace, plan)
    except Exception as error:
        summary["errors"].append("Frozen-source/input check: " + str(error))
        save_json(output / "summary.json", summary)
        return 1
    plots = {}
    for name, settings in plan["cases"].items():
        folder = workspace / name
        mesh = folder / MODEL / "matlab_mesh"
        result = {"steps": settings["steps"], "final_displacement_mm": settings["final_displacement_mm"],
                  "reference_source": settings["reference_source"]}
        values = {}
        for mode, source, regularization, equivalent in [
            ("oliver", folder / "reference_matlab_oliver", "oliver", "modified_mises")] + [
            (mode, folder / ("matlab_" + mode), "area" if mode == "area" else "oliver",
             "rankine" if mode == "rankine" else "modified_mises") for mode in settings["matlab_new_runs"]]:
            try:
                result[mode], values[mode] = matlab_check(source, mesh, settings, regularization, equivalent)
            except Exception as error:
                result[mode] = {"passed_execution_checks": False, "error": str(error)}
                summary["errors"].append(name + "/" + mode + ": " + str(error))
        try:
            result["abaqus"], values["abaqus"] = abaqus_check(folder / MODEL, settings)
        except Exception as error:
            result["abaqus"] = {"passed_execution_checks": False, "error": str(error), "adaptive_fallback": False}
            execution = folder / "abaqus_execution.json"
            if execution.exists():
                result["abaqus"]["execution_record"] = json.loads(execution.read_text())
            summary["errors"].append(name + "/abaqus: " + str(error))
        if "oliver" in values:
            for other in ("area", "rankine", "abaqus"):
                if other in values:
                    result[other + "_versus_oliver"] = comparison(values["oliver"], values[other])
        summary["cases"][name] = result
        plots[name] = values
    matched = [(name, values) for name, values in plots.items() if "oliver" in values and "abaqus" in values]
    if matched:
        fig, axes = plt.subplots(2, 2, figsize=(11, 7.5), squeeze=False)
        for axis, (name, values) in zip(axes.flat, matched):
            axis.plot(values["oliver"][:, 0], values["oliver"][:, 1] / 1000, color="#205b88", label="MATLAB, Oliver")
            axis.plot(values["abaqus"][:, 0], values["abaqus"][:, 1] / 1000, "--", color="#ba543a", label="Abaqus, Oliver")
            axis.set_title("%s: %s fixed increments" % (name.capitalize(), plan["cases"][name]["steps"]))
            axes_style(axis)
            axis.legend(frameon=False, fontsize=9)
        for axis in list(axes.flat)[len(matched):]:
            axis.set_visible(False)
        save_figure(fig, output, "matched_fixed_increment_responses")
    area = [(name, values) for name, values in plots.items() if "oliver" in values and "area" in values]
    if area:
        fig, axes = plt.subplots(1, len(area), figsize=(4.1 * len(area), 3.6), squeeze=False)
        for axis, (name, values) in zip(axes.flat, area):
            axis.plot(values["oliver"][:, 0], values["oliver"][:, 1] / 1000, color="#205b88", label="Oliver")
            axis.plot(values["area"][:, 0], values["area"][:, 1] / 1000, "--", color="#ba543a", label=r"$h=\sqrt{2A}$")
            axis.set_title(name.capitalize())
            axes_style(axis)
            axis.legend(frameon=False)
        save_figure(fig, output, "area_versus_oliver")
    coarse = plots.get("coarse", {})
    if "oliver" in coarse and "rankine" in coarse:
        fig, axis = plt.subplots(figsize=(6.1, 4.0))
        axis.plot(coarse["oliver"][:, 0], coarse["oliver"][:, 1] / 1000, color="#205b88", label="Modified von Mises")
        axis.plot(coarse["rankine"][:, 0], coarse["rankine"][:, 1] / 1000, "--", color="#ba543a", label="Maximum positive principal strain")
        axis.set_title("Same coarse mesh, Oliver width and %d fixed increments" % plan["cases"]["coarse"]["steps"])
        axes_style(axis)
        axis.legend(frameon=False)
        save_figure(fig, output, "equivalent_strain_comparison")
    summary["execution_checks_complete"] = not summary["errors"]
    summary["status"] = "complete_requires_scientific_interpretation" if not summary["errors"] else "incomplete_or_requires_review"
    save_json(output / "summary.json", summary)
    print(summary["status"] + ": " + str(output / "summary.json"))
    return 0 if not summary["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
