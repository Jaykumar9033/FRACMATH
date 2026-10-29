"""Run the additional 2D comparisons in fresh folders, one solve at a time.

Prepare first, inspect plan.json, then run the numerical stages after timing jobs.
Example:
  python softwarex/run_comparison_extension.py --workspace C:/runs/extension --stage prepare
  python softwarex/run_comparison_extension.py --workspace C:/runs/extension --stage abaqus
  python softwarex/run_comparison_extension.py --workspace C:/runs/extension --stage matlab
  python softwarex/run_comparison_extension.py --workspace C:/runs/extension --stage analyze

Fixed Abaqus increments are mandatory. A failed job is preserved and is not
restarted with adaptive increments. Use a new workspace for another attempt.
The default suite adds three Abaqus jobs, three area-width MATLAB jobs and one
Rankine MATLAB job. The existing exact Oliver MATLAB results are copied as
references, not counted as new runs. These jobs are not timing replicates.
The optional baseline case requires its separate preserved input source.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path(__file__).resolve().parent
CASES = ("baseline", "coarse", "medium", "fine")
MODEL = "Gregoire_3PB"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def fixed_input(text, steps):
    """Keep the original model; replace the single general-static schedule."""
    pattern = r"(?im)^\*static[^\r\n]*\r?\n([^\r\n]+)"
    matches = list(re.finditer(pattern, text))
    if len(matches) != 1:
        raise ValueError("Expected exactly one general-static step")
    previous = matches[0]
    values = [float(value.strip()) for value in previous.group(1).split(",") if value.strip()]
    if len(values) < 2 or abs(values[1] - 1.0) > 1.e-12:
        raise ValueError("Expected a unit-duration proportional loading step")
    if re.search(r"(?im)^\*amplitude|^\*include", text):
        raise ValueError("External includes/amplitudes require a separate inspection")
    # DIRECT without '=NO STOP' retains the normal equilibrium acceptance gate.
    replacement = "*Static, direct\n%.16g, 1.0" % (1.0 / steps)
    updated = text[:previous.start()] + replacement + text[previous.end():]
    pattern = r"(?im)(^\*Node Output[^\r\n]*nset=Load_Nodes[^\r\n]*\r?\n)([^\r\n]+)"
    match = re.search(pattern, updated)
    if not match or "RF2" not in match.group(2).upper():
        raise ValueError("Expected RF2 history output for Load_Nodes")
    components = [value.strip() for value in match.group(2).split(",") if value.strip()]
    if "U2" not in [value.upper() for value in components]:
        components.append("U2")
    updated = updated[:match.start(2)] + ", ".join(components) + updated[match.end(2):]
    if re.search(r"(?im)^\*static[^\r\n]*no\s*stop", updated):
        raise ValueError("NO STOP is forbidden for these comparisons")
    return updated


# This short script runs with Abaqus Python, which provides odbAccess.
# It exports the actual history times, not assumed times based on row numbers.
EXTRACT_SCHEDULE = r'''import json
from pathlib import Path
import re
import sys
from odbAccess import openOdb

odb_path, metadata_path, output_path = sys.argv[1:4]
metadata = json.loads(Path(metadata_path).read_text())
odb = openOdb(odb_path, readOnly=True)
try:
    step = odb.steps['Loading']
    def history(set_name, component, average):
        labels = {int(row[0]) for row in metadata['boundary_nodes'][set_name]}
        rows = []
        for name, region in step.historyRegions.items():
            integers = re.findall(r'\d+', name)
            if not integers or int(integers[-1]) not in labels:
                continue
            if component in region.historyOutputs:
                rows.append(dict(region.historyOutputs[component].data))
        if len(rows) != len(labels):
            raise ValueError('Missing node histories: %s %s' % (set_name, component))
        times = set(rows[0])
        for row in rows[1:]:
            if set(row) != times:
                raise ValueError('Node histories have different schedules')
        return {float(t): sum(float(row[t]) for row in rows) / (len(rows) if average else 1)
                for t in times}
    force = history('Load_Nodes', 'RF2', False)
    displacement = history('Load_Nodes', 'U2', True)
    left = history('CMOD1', 'U1', True)
    right = history('CMOD2', 'U1', True)
    if not set(force) == set(displacement) == set(left) == set(right):
        raise ValueError('Load and CMOD histories have different schedules')
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w') as stream:
        stream.write('normalized_time,displacement_mm,cmod_mm,load_N\n')
        for t in sorted(force):
            stream.write('%.17g,%.17g,%.17g,%.17g\n' %
                         (t, displacement[t], abs(right[t]-left[t]), -force[t]))
    with (output.parent / 'abaqus_load_cmod.csv').open('w') as stream:
        stream.write('# cmod[mm], load[N]\n')
        for t in sorted(force):
            stream.write('%.17g,%.17g\n' % (abs(right[t]-left[t]), -force[t]))
finally:
    odb.close()
'''


def prepare(args):
    if args.workspace.exists() and any(args.workspace.iterdir()):
        raise ValueError("Preparation needs an empty new workspace")
    if "baseline" in args.cases and args.rerun_root is None:
        raise ValueError("Provide --rerun-root for the preserved exact baseline input")
    args.workspace.mkdir(parents=True, exist_ok=True)
    snapshot = args.workspace / "source_snapshot"
    snapshot.mkdir()
    # The repository uses primary sources; an extracted study package uses
    # their identical supplied copies in reproducibility/.
    locations = (("3pb/matlab/solver_main_3pb.m", "reproducibility/2d/solver_main_3pb.m"),
                 ("3pb/abaqus/cdm_umat_2d_OLIVER_T3_FAST.for", "reproducibility/abaqus/cdm_umat_2d_OLIVER_T3_FAST.for"),
                 ("3pb/abaqus/run_3pb_abaqus_OLIVER_T3_FAST.py", "reproducibility/abaqus/run_3pb_abaqus_OLIVER_T3_FAST.py"))
    sources = [ROOT / primary if (ROOT / primary).exists() else PACKAGE / supplied
               for primary, supplied in locations]
    sources += [Path(__file__).resolve(), PACKAGE / "analyze_comparison_extension.py"]
    for source in sources:
        shutil.copy2(source, snapshot / source.name)
    plan = {"created_utc": datetime.now(timezone.utc).isoformat(),
            "status": "prepared_not_executed", "execution": "sequential",
            "increment_policy": "fixed for both; no adaptive fallback; no NO STOP",
            "abaqus_cpus": 1, "matlab_threads": 1,
            "timing_scope": "Single observations; not replacements for repeated timing study",
            "source_sha256": {path.name: digest(path) for path in snapshot.iterdir()},
            "cases": {}, "limitations": [
                "Matching increments does not make the nonlinear algorithms identical.",
                "MATLAB updates damage after solving at the previous damage state.",
                "Rankine changes the multiaxial damage surface; fc/ft has no role in that option."]}
    for name in args.cases:
        if name == "baseline":
            original = args.rerun_root / "baseline/abaqus/Gregoire_3PB"
            mesh = original / "matlab_mesh"
            reference = args.rerun_root / "baseline/matlab_10000"
            steps, displacement = 10000, -0.2
        else:
            archived = args.mesh_study / name
            original = archived / "abaqus/diagnostics"
            mesh = archived / "mesh"
            reference = archived / ("matlab_oliver_%d" % args.mesh_steps)
            if args.rerun_root is not None:
                candidate = args.rerun_root / "mesh_study" / name / ("matlab_oliver_%d" % args.mesh_steps)
                if (candidate / "verified_state.mat").exists():
                    reference = candidate
            steps, displacement = args.mesh_steps, -0.1
        folder = args.workspace / name
        job = folder / MODEL
        job.mkdir(parents=True)
        shutil.copytree(mesh, job / "matlab_mesh")
        metadata_path = job / "matlab_mesh/mesh_metadata.json"
        metadata = json.loads(metadata_path.read_text())
        original_metadata_sha256 = digest(metadata_path)
        metadata["original_increment_metadata"] = metadata.get("max_increment")
        metadata["max_increment"] = 1.0 / steps
        metadata["increment_mode"] = "fixed"
        save_json(metadata_path, metadata)
        source_input = original / (MODEL + ".inp")
        original_text = source_input.read_text()
        load = re.search(r"(?im)^Load_Nodes\s*,\s*2\s*,\s*2\s*,\s*([-+\d.eE]+)", original_text)
        if not load or abs(float(load.group(1)) - displacement) > 1.e-12:
            raise ValueError("Original load endpoint differs: " + str(source_input))
        shutil.copy2(source_input, folder / "original_input.inp")
        (job / (MODEL + ".inp")).write_text(fixed_input(original_text, steps))
        shutil.copy2(original / "oliver_t3_gradN.dat", job / "oliver_t3_gradN.dat")
        (job / "abaqus_v6.env").write_text('compile_fortran += ["/names:lowercase"]\n')
        (job / "extract_schedule.py").write_text(EXTRACT_SCHEDULE)
        reference_copy = folder / "reference_matlab_oliver"
        reference_copy.mkdir()
        for filename in ("matlab_load_cmod.csv", "matlab_step_diagnostics.csv",
                         "matlab_energy_history.csv", "matlab_timing.txt", "verified_state.mat"):
            source = reference / filename
            if source.exists():
                shutil.copy2(source, reference_copy / filename)
        if not (reference_copy / "verified_state.mat").exists():
            raise ValueError("Missing complete reference state: " + str(reference))
        plan["cases"][name] = {"steps": steps, "final_displacement_mm": displacement,
            "original_input": str(source_input), "original_input_sha256": digest(source_input),
            "fixed_input_sha256": digest(job / (MODEL + ".inp")),
            "mesh_sha256": {p.name: digest(p) for p in (job / "matlab_mesh").iterdir()
                            if p.suffix in (".txt", ".json")},
            "original_metadata_sha256": original_metadata_sha256,
            "oliver_table_sha256": digest(job / "oliver_t3_gradN.dat"),
            "reference_source": str(reference),
            "reference_sha256": {p.name: digest(p) for p in reference_copy.iterdir()},
            "matlab_new_runs": (["area"] + (["rankine"] if name == "coarse" else []))
                               if name != "baseline" else []}
    save_json(args.workspace / "plan.json", plan)
    print("Prepared %d fixed Abaqus jobs and %d new MATLAB jobs; no jobs executed." %
          (len(plan["cases"]), sum(len(c["matlab_new_runs"]) for c in plan["cases"].values())))


def run_logged(command, folder, env, log):
    print("Starting:", log, flush=True)
    started = time.monotonic()
    with log.open("w", encoding="utf-8") as stream:
        result = subprocess.run(command, cwd=folder, env=env, stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError("Process failed; inspect " + str(log))
    return time.monotonic() - started


def abq_command(executable, arguments):
    return (["cmd.exe", "/d", "/c"] if os.name == "nt" else []) + [executable] + arguments


def validate_frozen_inputs(workspace, plan):
    snapshot = workspace / "source_snapshot"
    for name, expected in plan["source_sha256"].items():
        if digest(snapshot / name) != expected:
            raise ValueError("Frozen source changed: " + name)
    for name, settings in plan["cases"].items():
        folder = workspace / name
        if digest(folder / MODEL / (MODEL + ".inp")) != settings["fixed_input_sha256"]:
            raise ValueError("Fixed input changed: " + name)
        for filename, expected in settings["mesh_sha256"].items():
            if digest(folder / MODEL / "matlab_mesh" / filename) != expected:
                raise ValueError("Mesh changed: " + name + "/" + filename)
        if digest(folder / MODEL / "oliver_t3_gradN.dat") != settings["oliver_table_sha256"]:
            raise ValueError("Oliver table changed: " + name)
        for filename, expected in settings["reference_sha256"].items():
            if digest(folder / "reference_matlab_oliver" / filename) != expected:
                raise ValueError("Copied reference changed: " + name + "/" + filename)


def run_abaqus(args, plan):
    executable = shutil.which("abaqus")
    if executable is None:
        raise RuntimeError("Abaqus is not on PATH")
    failures = []
    for name in args.cases:
        folder = args.workspace / name
        job = folder / MODEL
        status_path = folder / "abaqus_execution.json"
        if status_path.exists():
            previous = json.loads(status_path.read_text())
            if previous["status"] == "completed_requires_verification":
                print("Already executed:", name, flush=True)
                continue
            failures.append(name + ": preserved previous attempt; use a new workspace")
            continue
        status = {"status": "running", "started_utc": datetime.now(timezone.utc).isoformat(),
                  "fixed_steps": plan["cases"][name]["steps"], "adaptive_fallback": False}
        save_json(status_path, status)
        env = os.environ.copy()
        env["ABQ_OLIVER_TABLE"] = str(job / "oliver_t3_gradN.dat")
        env["ABQ_INCREMENT_MODE"] = "fixed"
        umat = args.workspace / "source_snapshot/cdm_umat_2d_OLIVER_T3_FAST.for"
        try:
            # Abaqus uses its configured Fortran environment, as in the original runs.
            status["launch_elapsed_s"] = run_logged(abq_command(executable,
                ["job=" + MODEL, "input=" + MODEL + ".inp", "user=" + str(umat),
                 "cpus=1", "mp_mode=threads", "interactive"]), job, env, folder / "abaqus_run.log")
            sta = job / (MODEL + ".sta")
            if not sta.exists() or "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" not in sta.read_text():
                raise RuntimeError("Fixed-increment analysis did not complete; inspect .msg/.sta")
            run_logged(abq_command(executable, ["python", "extract_schedule.py", MODEL + ".odb",
                str(job / "matlab_mesh/mesh_metadata.json"), str(job / "results/abaqus_schedule.csv")]),
                job, env, folder / "extract_schedule.log")
            status["status"] = "completed_requires_verification"
        except Exception as error:
            status["status"] = "failed_preserved_no_adaptive_fallback"
            status["error"] = str(error)
            failures.append(name + ": " + str(error))
        save_json(status_path, status)
    return failures


def run_matlab(args, plan):
    executable = shutil.which("matlab")
    if executable is None:
        raise RuntimeError("MATLAB is not on PATH")
    snapshot = args.workspace / "source_snapshot"
    failures = []
    for name in args.cases:
        settings = plan["cases"][name]
        for mode in settings["matlab_new_runs"]:
            folder = args.workspace / name / ("matlab_" + mode)
            if folder.exists():
                if (folder / "execution.json").exists() and json.loads((folder / "execution.json").read_text())["status"] == "completed_requires_verification":
                    print("Already executed:", folder, flush=True)
                    continue
                failures.append(str(folder) + ": preserved previous attempt; use a new workspace")
                continue
            folder.mkdir()
            env = os.environ.copy()
            env.update(FRACMATH_CASE_DIR=str(args.workspace / name / MODEL / "matlab_mesh"),
                FRACMATH_RESULTS_DIR=str(folder), FRACMATH_HEADLESS="1", FRACMATH_SELFTEST="0",
                FRACMATH_STEPS=str(settings["steps"]), FRACMATH_MAX_DISP=str(settings["final_displacement_mm"]),
                FRACMATH_REGULARIZATION="area" if mode == "area" else "oliver",
                FRACMATH_EQUIVALENT_STRAIN="rankine" if mode == "rankine" else "modified_mises",
                FRACMATH_THREADS="1", FRACMATH_BACKEND="cpu", FRACMATH_SIZE_SCALE="1")
            status = {"status": "running", "started_utc": datetime.now(timezone.utc).isoformat(), "mode": mode}
            save_json(folder / "execution.json", status)
            try:
                directory = str(snapshot).replace("'", "''")
                status["launch_elapsed_s"] = run_logged([executable, "-batch",
                    "addpath('%s');solver_main_3pb" % directory], folder, env, folder / "run.log")
                if not (folder / "verified_state.mat").exists():
                    raise RuntimeError("MATLAB did not save a complete state")
                status["status"] = "completed_requires_verification"
            except Exception as error:
                status["status"] = "failed_preserved"
                status["error"] = str(error)
                failures.append(str(folder) + ": " + str(error))
            save_json(folder / "execution.json", status)
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--rerun-root", type=Path)
    parser.add_argument("--mesh-study", type=Path, default=PACKAGE / "reproducibility/mesh_study")
    parser.add_argument("--mesh-steps", type=int, choices=(2000, 4000), default=2000,
                        help="Fixed increments for both programs; 4000 requires a separate fresh workspace")
    parser.add_argument("--cases", nargs="+", choices=CASES, default=["coarse", "medium", "fine"])
    parser.add_argument("--stage", choices=("prepare", "abaqus", "matlab", "analyze", "all"), default="prepare")
    args = parser.parse_args()
    args.workspace = args.workspace.resolve()
    if args.rerun_root is not None:
        args.rerun_root = args.rerun_root.resolve()
    if args.stage in ("prepare", "all"):
        prepare(args)
    plan = json.loads((args.workspace / "plan.json").read_text())
    if any(name not in plan["cases"] for name in args.cases):
        parser.error("Requested case was not prepared in this workspace")
    validate_frozen_inputs(args.workspace, plan)
    failures = []
    if args.stage in ("abaqus", "all"):
        failures += run_abaqus(args, plan)
    if args.stage in ("matlab", "all"):
        failures += run_matlab(args, plan)
    if args.stage in ("analyze", "all"):
        script = args.workspace / "source_snapshot/analyze_comparison_extension.py"
        result = subprocess.run([sys.executable, str(script), "--workspace", str(args.workspace)])
        if result.returncode:
            failures.append("Verification incomplete or requires review; read analysis/summary.json")
    if failures:
        print("Preserved failures:\n" + "\n".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
