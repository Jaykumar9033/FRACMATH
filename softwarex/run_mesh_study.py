"""Run the controlled 2D mesh study; preserve each run in its own directory.

Requires licensed MATLAB and Abaqus/Standard with a configured Fortran compiler.
Example: python softwarex/run_mesh_study.py --workspace C:/runs/mesh_study
Run stages sequentially for timing: build, matlab, abaqus. No jobs run together.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import hashlib
import platform
import psutil
from datetime import datetime, timezone
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path(__file__).resolve().parent
MATLAB_SOURCE = ROOT / "3pb/matlab"
ABAQUS_SOURCE = ROOT / "3pb/abaqus"
if not MATLAB_SOURCE.exists():
    MATLAB_SOURCE = PACKAGE / "reproducibility/2d"
    ABAQUS_SOURCE = PACKAGE / "reproducibility/abaqus"
SCALES = {"coarse": 1.0, "medium": 0.75, "fine": 0.5}


def command_abaqus(folder):
    executable = shutil.which("abaqus")
    if not executable:
        raise RuntimeError("Abaqus is not on PATH")
    command = [executable, "cae", "noGUI=run_3pb_abaqus_OLIVER_T3_FAST.py"]
    return ["cmd.exe", "/d", "/c"] + command if os.name == "nt" else command


def launch(command, folder, env, log):
    start = time.time()
    print("Starting %s" % log, flush=True)
    standard_peak = 0
    with log.open("w", encoding="utf-8") as stream:
        process = subprocess.Popen(command, cwd=folder, env=env,
                                   stdout=stream, stderr=subprocess.STDOUT)
        while process.poll() is None:
            try:
                children = psutil.Process(process.pid).children(recursive=True)
                standard_rss = sum(p.memory_info().rss for p in children
                                   if p.name().lower() == "standard.exe")
                standard_peak = max(standard_peak, standard_rss)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            time.sleep(1)
    if process.returncode:
        raise RuntimeError("Run failed (%d). Inspect %s" % (process.returncode, log))
    sampling = dict(launch_elapsed_s=time.time()-start,
                    standard_sampled_peak_working_set_MB=standard_peak/2**20 if standard_peak else None,
                    sampling_interval_s=1,
                    scope="Abaqus standard.exe descendant processes only; excludes CAE")
    log.with_suffix(".sampling.json").write_text(json.dumps(sampling, indent=2)+"\n")
    print("Completed in %.1f s: %s" % (time.time()-start, log), flush=True)


def abaqus_env(name, build_only, args):
    env = os.environ.copy()
    env.update(ABQ_MESH_SCALE=str(SCALES[name]), ABQ_U_FINAL=str(args.max_disp),
               ABQ_STUDY_BC="1", ABQ_BUILD_ONLY="1" if build_only else "0",
               ABQ_N_INC=str(args.steps), ABQ_CPUS="1", ABQ_AUTO_PLOT="0",
               ABQ_FIELD_FREQ=str(max(1, args.steps // 20)))
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--stage", choices=["build", "matlab", "abaqus", "all"], default="all")
    parser.add_argument("--meshes", nargs="+", choices=list(SCALES), default=list(SCALES))
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--max-disp", type=float, default=-0.1)
    parser.add_argument("--increment-checks", action="store_true")
    parser.add_argument("--fixed-fine-check", action="store_true")
    parser.add_argument("--regularizations", nargs="+", choices=["oliver", "fixed"], default=["oliver", "fixed"])
    parser.add_argument("--ifx-lowercase", action="store_true",
                        help="Add a local Abaqus Fortran symbol-name override for Intel ifx")
    args = parser.parse_args()
    if args.steps <= 0 or args.max_disp >= 0:
        parser.error("steps must be positive and max-disp must be negative")
    args.workspace = args.workspace.resolve()
    args.workspace.mkdir(parents=True, exist_ok=True)
    manifest = dict(mesh_scales=SCALES, steps=args.steps, max_disp_mm=args.max_disp,
                    boundary_conditions="Exact x=50 and 300 mm supports; top loading strip x=171.875 to 178.125 mm",
                    fixed_softening_reference_width_mm=1.25,
                    increment_checks=args.increment_checks,
                    fixed_fine_check=args.fixed_fine_check,
                    timing_execution="sequential processes, one computational thread/CPU")
    manifest["platform"] = platform.platform()
    manifest["processor"] = platform.processor()
    manifest["source_sha256"] = {
        source.name: hashlib.sha256(source.read_bytes()).hexdigest()
        for source in [MATLAB_SOURCE / "solver_main_3pb.m",
                       ABAQUS_SOURCE / "run_3pb_abaqus_OLIVER_T3_FAST.py",
                       ABAQUS_SOURCE / "cdm_umat_2d_OLIVER_T3_FAST.for"]}
    manifest["source_text_sha256"] = {
        source.name: hashlib.sha256(source.read_text().replace("\r\n", "\n").encode("utf-8")).hexdigest()
        for source in [MATLAB_SOURCE / "solver_main_3pb.m",
                       ABAQUS_SOURCE / "run_3pb_abaqus_OLIVER_T3_FAST.py",
                       ABAQUS_SOURCE / "cdm_umat_2d_OLIVER_T3_FAST.for"]}
    manifest_path = args.workspace / "run_manifest.json"
    invocations = []
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if previous["max_disp_mm"] != args.max_disp:
            raise RuntimeError("Use a new workspace when changing the prescribed displacement")
        invocations = previous.get("invocations", [])
        manifest["steps"] = previous["steps"]
        manifest["increment_checks"] = previous.get("increment_checks", False) or args.increment_checks
        manifest["fixed_fine_check"] = previous.get("fixed_fine_check", False) or args.fixed_fine_check
    invocations.append(dict(utc=datetime.now(timezone.utc).isoformat(), stage=args.stage,
                            meshes=args.meshes, steps=args.steps,
                            regularizations=args.regularizations,
                            source_sha256=manifest["source_sha256"],
                            source_text_sha256=manifest["source_text_sha256"]))
    manifest["invocations"] = invocations
    manifest_path.write_text(json.dumps(manifest, indent=2)+"\n")
    for name in args.meshes:
        folder = args.workspace / name
        folder.mkdir(exist_ok=True)
        for source in ("run_3pb_abaqus_OLIVER_T3_FAST.py", "cdm_umat_2d_OLIVER_T3_FAST.for"):
            shutil.copy2(ABAQUS_SOURCE / source, folder / source)
        if args.ifx_lowercase:
            (folder / "abaqus_v6.env").write_text('compile_fortran += ["/names:lowercase"]\n')
        mesh = folder / "Gregoire_3PB/matlab_mesh"
        if args.stage in ("build", "all"):
            metadata = mesh / "mesh_metadata.json"
            if not metadata.exists():
                launch(command_abaqus(folder), folder, abaqus_env(name, True, args), folder / "build.log")
            data = json.loads(metadata.read_text())
            if data["mesh_scale"] != SCALES[name] or not data["study_boundary_conditions"]:
                raise RuntimeError("Existing mesh settings differ: %s" % metadata)
        if args.stage in ("matlab", "all"):
            if not mesh.exists():
                raise RuntimeError("Build mesh first: %s" % name)
            runs = [(mode, args.steps) for mode in args.regularizations]
            if args.increment_checks and name in ("coarse", "fine"):
                runs.append(("oliver", 2*args.steps))
            if args.fixed_fine_check and name == "fine":
                runs.append(("fixed", 2*args.steps))
            for regularization, steps in runs:
                result = folder / ("matlab_%s_%d" % (regularization, steps))
                if (result / "verified_state.mat").exists() and (result / "matlab_energy_history.csv").exists():
                    settings = loadmat(result / "verified_state.mat", variable_names=["p"], simplify_cells=True)["p"]
                    if abs(settings["max_disp"]-args.max_disp) > 1.e-12 or settings["num_steps"] != steps or settings["regularization"] != regularization:
                        raise RuntimeError("Existing MATLAB run settings differ: %s" % result)
                    print("Already complete: %s" % result, flush=True)
                    continue
                result.mkdir(exist_ok=True)
                env = os.environ.copy()
                env.update(FRACMATH_CASE_DIR=str(mesh), FRACMATH_RESULTS_DIR=str(result),
                           FRACMATH_HEADLESS="1", FRACMATH_STEPS=str(steps),
                           FRACMATH_MAX_DISP=str(args.max_disp), FRACMATH_REGULARIZATION=regularization,
                           FRACMATH_FIXED_WIDTH="1.25", FRACMATH_SELFTEST="0")
                solver_dir = str(MATLAB_SOURCE).replace("'", "''")
                launch(["matlab", "-batch", "addpath('%s'); solver_main_3pb" % solver_dir],
                       folder, env, result / "run.log")
        if args.stage in ("abaqus", "all"):
            result = folder / "Gregoire_3PB/results/abaqus_load_cmod.csv"
            if result.exists():
                settings = json.loads((mesh / "mesh_metadata.json").read_text())
                if abs(settings["max_displacement_mm"]-args.max_disp) > 1.e-12 or abs(settings["max_increment"]-1/args.steps) > 1.e-12:
                    raise RuntimeError("Existing Abaqus increment settings differ; use a new workspace")
                print("Already complete: %s" % result, flush=True)
                continue
            launch(command_abaqus(folder), folder, abaqus_env(name, False, args), folder / "abaqus.log")
            if not result.exists():
                raise RuntimeError("CAE did not export the completed response; inspect abaqus.rpy and use ABQ_EXTRACT_ONLY=1: " + name)


if __name__ == "__main__":
    main()
