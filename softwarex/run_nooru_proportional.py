"""Run the illustrative proportional case with strict accepted equilibrium.

The mesh and material are retained; numerical tangent, irreversible damage
history and rejected-trial bisection follow the pure-tension verification.
This proportional path is not the published experimental 4a/4c sequence.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import numpy as np
from run_nooru_mesh_study import create_solver


def main():
    package = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--steps", type=int, default=900)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--snapshots", action="store_true")
    parser.add_argument("--safeguarded", action="store_true")
    args = parser.parse_args()
    folder = args.workspace.resolve()
    if (folder/"completion.json").exists():
        raise ValueError("Use a new workspace to preserve the existing run")
    folder.mkdir(parents=True, exist_ok=True)
    mesh = package.parent/"Noor mohammad/Mesh"
    names = ["Job-1_nodes.txt", "Job-1_elements.txt"] + [
        "Job-1_%s_nodes.txt" % side for side in ["top", "bottom", "left", "right"]]
    hashes = {}
    for name in names:
        shutil.copy2(mesh/name, folder/name)
        hashes[name] = hashlib.sha256((folder/name).read_bytes()).hexdigest()
    source = args.source or package.parent/"Noor mohammad/Mesh/damage_static.m"
    if args.source is None and not source.exists():
        source=package/"current_source/damage_static.m"
    create_solver(source, folder/"damage_static.m")
    if args.snapshots:
        solver=folder/"damage_static.m"
        text=solver.read_text(encoding="utf-8")
        text=text.replace("(mod(s,snapshot_stride)==0 || s==1 || s==nIncr)",
                          "any(abs(lambda_load-[29 37 41 53 75 127 275 407 900]/900)<1e-12)")
        solver.write_text(text,encoding="utf-8")
    if args.safeguarded:
        from safeguard_nooru_solver import safeguard_solver
        safeguard_solver(folder/"damage_static.m")
    script = """maxNumCompThreads(1);
opts=struct('load_path','4c','nIncr',%d,'Uy_end',0.5,'gamma',0.6, ...
 'E',29000,'nu',0.2,'ft',3,'GF',0.11,'k',10, ...
 'show_live',false,'save_all_increment_geometry',false,'show_mesh',false, ...
 'save_show_mesh',false,'print_stride',20,'maxIter',150, ...
 'use_line_search',true,'tol',1e-6,'strict_equilibrium',true, ...
 'maxLineSearch',12,'out_dir',pwd);
damage_static('Job-1',opts);
""" % args.steps
    if args.snapshots:
        script=script.replace("'save_all_increment_geometry',false", "'save_all_increment_geometry',true")
        script=script.replace("'save_show_mesh',false", "'save_show_mesh',true,'save_when_no_full_damage',true,'damage_clim',[0.95 1],'damage_clim_mode','full'")
    if args.safeguarded:
        script=script.replace("'maxLineSearch',12", "'maxLineSearch',24").replace("'print_stride',20", "'print_stride',5")
    (folder/"run_case.m").write_text(script, encoding="utf-8")
    record = dict(geometry_mm=[200,200,50], notch_depth_mm=20,
                  notch_width_mm=5, initial_intervals=args.steps,
                  final_top_displacement_mm=.5, shear_tension_ratio=.6,
                  material=dict(E_MPa=29000,nu=.2,ft_MPa=3,GF_N_per_mm=.11,k=10),
                  equilibrium_tolerance=1e-6, mesh_sha256=hashes,
                  safeguarded_solver=args.safeguarded,
                  checkpoints="accepted_checkpoint.mat" if args.safeguarded else None,
                  energy_convention="total tensile work including the elastic part",
                  selected_snapshot_nominal_increments=[29,37,41,53,75,127,275,407,900] if args.snapshots else [],
                  generated_solver_sha256=hashlib.sha256((folder/"damage_static.m").read_bytes()).hexdigest(),
                  scope="Proportional illustrative controls, not experimental 4a/4c validation.")
    (folder/"invocation.json").write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    record.update(completed=False,in_progress=True,driver_pid=os.getpid())
    (folder/"completion.json").write_text(json.dumps(record,indent=2)+"\n",encoding="utf-8")
    with (folder/"console.log").open("w", encoding="utf-8") as stream:
        process = subprocess.run(["matlab", "-batch", "run_case"], cwd=folder,
                                 stdout=stream, stderr=subprocess.STDOUT)
    record.update(return_code=process.returncode, completed=False,in_progress=False)
    if process.returncode == 0:
        history = np.genfromtxt(folder/"Job-1_fast_NR_results.csv", delimiter=",", names=True,
                               usecols=(0,1,2,3,11))
        targets = np.loadtxt(folder/"accepted_targets.csv", delimiter=",")
        passed = (len(history)==len(targets)
                  and all(np.isfinite(history[field]).all() for field in history.dtype.names)
                  and np.max(history["relative_residual"])<=1e-6
                  and np.isclose(history["delta_mm"][-1], .5)
                  and np.all(np.diff(history["delta_mm"])>0)
                  and np.allclose(history["delta_s_mm"], .6*history["delta_mm"]))
        record.update(completed=bool(passed), accepted_increments=len(history),
                      maximum_relative_residual=float(history["relative_residual"].max()),
                      rejected_trials=int(np.loadtxt(folder/"rejected_trial_count.csv")))
    (folder/"completion.json").write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(record, indent=2))
    if not record["completed"]:
        raise SystemExit("No validated complete proportional history; inspect console.log")


if __name__ == "__main__":
    main()
