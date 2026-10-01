"""Validate completed mesh-study histories and regenerate data and figures."""
import argparse
import csv
import json
import hashlib
from pathlib import Path
import re
import numpy as np
from scipy.io import loadmat
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from compare_solver_diagnostics import summarize

HERE = Path(__file__).resolve().parent
MESHES = ("coarse", "medium", "fine")
COLORS = ("#205b88", "#d1773f", "#537d48")
STYLES = ("-", "--", "-.")


def number(pattern, text, required=True):
    match = re.search(pattern, text)
    if not match:
        if required:
            raise ValueError("Missing timing field: " + pattern)
        return None
    return float(match.group(1))


def interpolate(cmod, values, target):
    if np.any(np.diff(cmod) < -1e-8):
        raise ValueError("CMOD is not monotone; explicit branch selection is required")
    if cmod[-1] < target:
        raise ValueError("Run did not reach requested common CMOD %.3f" % target)
    return float(np.interp(target, cmod, values))


def matlab_result(folder, metadata, target):
    load = np.loadtxt(folder / "matlab_load_cmod.csv", delimiter=",", comments="#")
    energy = np.genfromtxt(folder / "matlab_energy_history.csv", delimiter=",", names=True)
    diagnostic = np.genfromtxt(folder / "matlab_step_diagnostics.csv", delimiter=",", names=True)
    if len(load) != len(energy) or len(load) != len(diagnostic):
        raise ValueError("History lengths differ: %s" % folder)
    if not np.all(np.isfinite(load)) or not np.all(diagnostic["old_damage_converged"] == 1):
        raise ValueError("Invalid response or failed old-damage solve: %s" % folder)
    for data in (energy, diagnostic):
        if any(not np.all(np.isfinite(data[field])) for field in data.dtype.names):
            raise ValueError("Non-finite energy or diagnostic values: %s" % folder)
    dissipation = energy["damage_dissipation_Nmm"]
    if np.any(np.diff(dissipation) < -1.e-7):
        raise ValueError("Damage dissipation decreased")
    peak = int(np.argmax(load[:, 1]))
    timing = (folder / "matlab_timing.txt").read_text()
    work = interpolate(energy["cmod_mm"], energy["external_work_Nmm"], target)
    balance = interpolate(energy["cmod_mm"], energy["energy_balance_error_Nmm"], target)
    row = dict(mesh=metadata["mesh"], elements=metadata["elements"], dofs=metadata["dofs"],
                steps=len(load), peak_load_N=float(load[peak, 1]),
                peak_cmod_mm=float(load[peak, 0]),
                dissipation_at_common_cmod_Nmm=interpolate(energy["cmod_mm"], dissipation, target),
                external_work_at_common_cmod_Nmm=work,
                energy_balance_error_at_common_cmod_percent=100*balance/max(work, 1.e-12),
                peak_post_damage_relative_residual=float(diagnostic["post_damage_relative_residual"][peak]),
                max_post_damage_relative_residual=float(np.max(diagnostic["post_damage_relative_residual"])),
                wall_s=number(r"Solver wall-clock:\s*([\d.]+)", timing),
                factorization_s=number(r"factorization:\s*([\d.]+)", timing),
                assembly_s=number(r"assembly:\s*([\d.]+)", timing),
                damage_s=number(r"damage:\s*([\d.]+)", timing),
                solve_s=number(r"solve:\s*([\d.]+)", timing),
                peak_process_working_set_MB=number(r"Peak process working set:\s*([\d.]+)", timing, False))

    state = loadmat(folder / "verified_state.mat", variable_names=["nodes", "elems", "snap_peak"], simplify_cells=True)
    triangles = state["nodes"][state["elems"].astype(int)-1]
    centers = triangles.mean(axis=1)
    first, second = triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0]
    areas = np.abs(first[:, 0]*second[:, 1]-first[:, 1]*second[:, 0])/2
    damaged = state["snap_peak"]["omega"] >= .95
    total = float(areas[damaged].sum())
    central = np.abs(centers[:, 0]-175) <= 25
    row["peak_high_damage_elements"] = int(damaged.sum())
    row["peak_high_damage_area_mm2"] = total
    row["peak_high_damage_area_in_refined_zone_fraction"] = float(areas[damaged & central].sum()/total) if total else None
    row["peak_high_damage_centroid_y_min_mm"] = float(centers[damaged, 1].min()) if total else None
    row["peak_high_damage_centroid_y_max_mm"] = float(centers[damaged, 1].max()) if total else None
    angles = []
    for corner in range(3):
        a = triangles[:, (corner+1)%3]-triangles[:, corner]
        b = triangles[:, (corner+2)%3]-triangles[:, corner]
        cosine = np.einsum("ij,ij->i", a, b)/(np.linalg.norm(a, axis=1)*np.linalg.norm(b, axis=1))
        angles.append(np.degrees(np.arccos(np.clip(cosine, -1, 1))))
    minimum_angles = np.min(angles, axis=0)
    row["mesh_minimum_triangle_angle_deg"] = float(minimum_angles.min())
    row["peak_high_damage_minimum_triangle_angle_deg"] = float(minimum_angles[damaged].min()) if total else None
    return row


def spread(values):
    a = np.asarray(values)
    return float(100*(np.max(a)-np.min(a))/np.mean(a))


def collect(workspace, target, steps, require_abaqus):
    result = dict(common_cmod_mm=target, main_steps=steps, meshes=[], matlab=[], abaqus=[], increment_checks=[])
    for name in MESHES:
        case = workspace / name
        mesh_folder = case / "Gregoire_3PB/matlab_mesh"
        if not mesh_folder.exists():
            mesh_folder = case / "mesh"
        metadata = json.loads((mesh_folder / "mesh_metadata.json").read_text())
        metadata["mesh"] = name
        for support, expected_x in (("Support_Left", 50), ("Support_Right", 300)):
            nodes = metadata["boundary_nodes"][support]
            if len(nodes) != 1 or abs(nodes[0][1]-expected_x) > 1.e-8:
                raise ValueError("Support coordinate changed across meshes")
        loading = np.asarray(metadata["boundary_nodes"]["Load_Nodes"])
        if (len(loading) < 2 or abs(loading[:, 1].min()-171.875) > 1.e-8
                or abs(loading[:, 1].max()-178.125) > 1.e-8
                or not np.allclose(loading[:, 2], 100, atol=1.e-8, rtol=0)):
            raise ValueError("Loading strip changed across meshes")
        for lip, x in (("CMOD1", 173.75), ("CMOD2", 176.25)):
            points = metadata["boundary_nodes"][lip]
            if len(points) != 1 or abs(points[0][1]-x) > 1.e-8 or abs(points[0][2]) > 1.e-8:
                raise ValueError("CMOD measurement coordinate changed across meshes")
        result["meshes"].append(metadata)
        for mode in ("oliver", "fixed"):
            folder = case / ("matlab_%s_%d" % (mode, steps))
            row = matlab_result(folder, metadata, target)
            row["regularization"] = mode
            result["matlab"].append(row)
        for folder in sorted(case.glob("matlab_*_*")):
            mode, count = folder.name.split("_")[1:]
            if int(count) == steps or not (folder / "matlab_energy_history.csv").exists():
                continue
            row = matlab_result(folder, metadata, target)
            row["regularization"] = mode
            base = next(r for r in result["matlab"] if r["mesh"] == name and r["regularization"] == mode)
            row["peak_change_percent"] = 100*(row["peak_load_N"]-base["peak_load_N"])/base["peak_load_N"]
            row["dissipation_change_percent"] = 100*(row["dissipation_at_common_cmod_Nmm"]-base["dissipation_at_common_cmod_Nmm"])/base["dissipation_at_common_cmod_Nmm"]
            result["increment_checks"].append(row)
        abq = case / "Gregoire_3PB"
        if not abq.exists():
            abq = case / "abaqus"
        msg_path = abq / "diagnostics/Gregoire_3PB.msg"
        if not msg_path.exists():
            msg_path = abq / "Gregoire_3PB.msg"
        if msg_path.exists():
            paired = summarize(case / ("matlab_oliver_%d/matlab_timing.txt" % steps), msg_path)["abaqus"]
            paired.update(mesh=name, dofs=metadata["dofs"], elements=metadata["elements"])
            curve = np.loadtxt(abq / "results/abaqus_load_cmod.csv", delimiter=",", comments="#")
            if curve.ndim != 2 or curve.shape[1] != 2 or not np.all(np.isfinite(curve)) or np.max(curve[:, 1]) <= 0:
                raise ValueError("Invalid Abaqus response: " + name)
            job_log = msg_path.with_suffix(".log").read_text(errors="replace")
            loaded = re.search(r"UMAT FAST:\s*Oliver T3 gradN table loaded, n=\s*(\d+)", job_log)
            if not loaded or int(loaded.group(1)) != metadata["elements"] or "using Abaqus CELENT fallback" in job_log:
                raise ValueError("Abaqus gradient-table initialization failed: " + name)
            paired["gradient_rows_loaded"] = int(loaded.group(1))
            paired["response_rows"] = len(curve)
            peak = int(np.argmax(curve[:, 1]))
            paired["peak_load_N"] = float(curve[peak, 1])
            paired["peak_cmod_mm"] = float(curve[peak, 0])
            matching_matlab = next(r for r in result["matlab"] if r["mesh"] == name and r["regularization"] == "oliver")
            paired["matlab_peak_load_difference_percent"] = 100*(matching_matlab["peak_load_N"]-paired["peak_load_N"])/paired["peak_load_N"]
            sampling_file = case / "abaqus.sampling.json"
            paired["sampled_standard_working_set_MB"] = json.loads(sampling_file.read_text())["standard_sampled_peak_working_set_MB"] if sampling_file.exists() else None
            result["abaqus"].append(paired)
        elif require_abaqus:
            raise ValueError("Abaqus job missing: " + name)
    manifest = workspace / "matlab_mesh_before_abaqus_sha256.json"
    if manifest.exists():
        for relative, expected in json.loads(manifest.read_text()).items():
            path = workspace / relative
            if not path.exists():
                path = workspace / relative.replace("/Gregoire_3PB/matlab_mesh/", "/mesh/")
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError("MATLAB/Abaqus mesh changed: " + relative)
        result["matching_mesh_hashes_verified"] = True
    result["mesh_spreads_percent"] = {}
    for mode in ("oliver", "fixed"):
        rows = [r for r in result["matlab"] if r["regularization"] == mode]
        result["mesh_spreads_percent"][mode] = {
            "peak_load": spread([r["peak_load_N"] for r in rows]),
            "dissipation": spread([r["dissipation_at_common_cmod_Nmm"] for r in rows])}
    refined_spreads = {}
    for mode in ("oliver", "fixed"):
        refined = [r for r in result["increment_checks"] if r["regularization"] == mode and r["steps"] == 2*steps]
        if len(refined) == 3 and {r["mesh"] for r in refined} == set(MESHES):
            refined_spreads[mode] = {
                "peak_load": spread([r["peak_load_N"] for r in refined]),
                "dissipation": spread([r["dissipation_at_common_cmod_Nmm"] for r in refined])}
    if len(refined_spreads) == 2:
        result["refined_mesh_spreads_percent"] = refined_spreads
    return result


def figures(workspace, result, out):
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, grid = plt.subplots(3, 2, figsize=(8.3, 10.5), layout="constrained")
    axes = grid[0]
    for ax, mode, title in zip(axes, ("oliver", "fixed"), ("Oliver regularization", "Fixed stress-strain softening")):
        for name, color, style in zip(MESHES, COLORS, STYLES):
            folder = workspace / name / ("matlab_%s_%d" % (mode, result["main_steps"]))
            curve = np.loadtxt(folder / "matlab_load_cmod.csv", delimiter=",", comments="#")
            row = next(r for r in result["matlab"] if r["mesh"] == name and r["regularization"] == mode)
            ax.plot(curve[:, 0], curve[:, 1]/1000, color=color, ls=style, lw=1.6,
                    label="%s: %s elements" % (name, format(row["elements"], ",")))
        ax.set(xlabel="CMOD (mm)", ylabel="load (kN)", title=title, xlim=(0, .15), ylim=(0, None))
        ax.grid(alpha=.18)
        ax.legend(frameon=False, fontsize=10)
    axes = grid[1]
    for mode, color, marker in (("oliver", COLORS[0], "o"), ("fixed", COLORS[1], "s")):
        rows = [r for r in result["matlab"] if r["regularization"] == mode]
        x = [r["dofs"] for r in rows]
        label = "Oliver" if mode == "oliver" else "Fixed law"
        axes[0].plot(x, [r["peak_load_N"]/1000 for r in rows], marker=marker, color=color, label=label)
        axes[1].plot(x, [r["dissipation_at_common_cmod_Nmm"] for r in rows], marker=marker, color=color, label=label)
    axes[0].set(ylabel="peak load (kN)")
    axes[1].set(ylabel="damage dissipation (N mm)", title="At CMOD = %.2f mm" % result["common_cmod_mm"])
    for ax in axes:
        ax.set_xlabel("degrees of freedom")
        ax.ticklabel_format(axis="x", style="sci", scilimits=(0, 0))
        ax.grid(alpha=.18)
        ax.legend(frameon=False)
    if result["abaqus"]:
        axes = grid[2]
        rows = [r for r in result["matlab"] if r["regularization"] == "oliver"]
        abq = result["abaqus"]
        axes[0].plot([r["dofs"] for r in rows], [r["wall_s"] for r in rows], "o-", color=COLORS[0], label="MATLAB wall")
        axes[0].plot([r["dofs"] for r in rows], [r["factorization_s"] for r in rows], "o--", color=COLORS[0], label="MATLAB factorization")
        axes[0].plot([r["dofs"] for r in abq], [r["wall_s"] for r in abq], "s-", color=COLORS[1], label="Abaqus wall")
        axes[0].plot([r["dofs"] for r in abq], [r["summed_solver_elapsed_s"] for r in abq], "s--", color=COLORS[1], label="Abaqus sparse solver")
        axes[0].set(xlabel="degrees of freedom", ylabel="elapsed time (s)", title="Measured costs; algorithms differ")
        axes[0].legend(frameon=False, fontsize=10)
        fine_matlab = workspace / "fine" / ("matlab_oliver_%d/matlab_load_cmod.csv" % result["main_steps"])
        folder = workspace / "fine/Gregoire_3PB/results"
        if not folder.exists():
            folder = workspace / "fine/abaqus/results"
        for path, color, style, label in (
            (fine_matlab, COLORS[0], "-", "MATLAB, fixed steps"),
            (folder / "abaqus_load_cmod.csv", COLORS[1], "--", "Abaqus, adaptive steps")):
            if path.exists():
                curve = np.loadtxt(path, delimiter=",", comments="#")
                axes[1].plot(curve[:, 0], curve[:, 1]/1000, color=color, ls=style, label=label)
        axes[1].set(xlabel="CMOD (mm)", ylabel="load (kN)", title="Fine mesh: response check", xlim=(0, .15), ylim=(0, None))
        axes[1].legend(frameon=False, fontsize=10)
        for ax in axes:
            ax.grid(alpha=.18)
    else:
        for ax in grid[2]:
            ax.set_visible(False)
    for label, ax in zip("abcdef", grid.flat):
        if ax.get_visible():
            ax.text(-.17, 1.06, "("+label+")", transform=ax.transAxes, fontweight="bold")
    fig.savefig(out / "mesh_study_overview.png", dpi=300, bbox_inches="tight")
    fig.savefig(out / "mesh_study_overview.pdf", bbox_inches="tight")
    plt.close(fig)
    if len(result["abaqus"]) == 3:
        fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), layout="constrained")
        for ax, name in zip(axes, MESHES):
            abq_folder = workspace / name / "Gregoire_3PB/results"
            if not abq_folder.exists():
                abq_folder = workspace / name / "abaqus/results"
            files = [(workspace / name / ("matlab_oliver_%d/matlab_load_cmod.csv" % result["main_steps"]), "MATLAB", "-", COLORS[0]),
                     (abq_folder / "abaqus_load_cmod.csv", "Abaqus", "--", COLORS[1])]
            for path, label, style, color in files:
                curve = np.loadtxt(path, delimiter=",", comments="#")
                ax.plot(curve[:, 0], curve[:, 1]/1000, ls=style, color=color, label=label)
            ax.set(title=name.capitalize()+" mesh", xlabel="CMOD (mm)", ylabel="load (kN)", xlim=(0, .15), ylim=(0, None))
            ax.grid(alpha=.18)
            ax.legend(frameon=False, fontsize=10)
        fig.savefig(out / "mesh_study_code_comparison.png", dpi=250, bbox_inches="tight")
        fig.savefig(out / "mesh_study_code_comparison.pdf", bbox_inches="tight")
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=HERE / "reproducibility/mesh_study")
    parser.add_argument("--output", type=Path, default=HERE / "reproducibility/mesh_study")
    parser.add_argument("--figures", type=Path, default=HERE / "figures")
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--common-cmod", type=float, default=.1)
    parser.add_argument("--matlab-only", action="store_true")
    args = parser.parse_args()
    result = collect(args.workspace, args.common_cmod, args.steps, not args.matlab_only)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(result, indent=2)+"\n")
    for key in ("matlab", "abaqus", "increment_checks"):
        rows = result[key]
        if rows:
            with (args.output / (key+"_summary.csv")).open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
    figures(args.workspace, result, args.figures)
    print(json.dumps({"mesh_spreads_percent": result["mesh_spreads_percent"],
                      "increment_checks": result["increment_checks"]}, indent=2))


if __name__ == "__main__":
    main()
