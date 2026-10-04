"""Inspect a completed separate profile without assigning unknown phases.

The named assembly rows and user-library self samples are disjoint. They
are profile estimates, not complete material/assembly wall-clock timers.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True,
                        help="Matching unprofiled Abaqus job folder")
    args = parser.parse_args()
    folder = args.workspace.resolve()
    job = folder/"Gregoire_3PB"
    manifest = json.loads((folder/"profile_manifest.json").read_text(encoding="utf-8"))
    if not all(manifest.get(key)==0 for key in ["collection_return_code",
            "summary_export_return_code", "hotspots_export_return_code"]):
        raise ValueError("Profile collection or report export failed")
    if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" not in (job/"Gregoire_3PB.sta").read_text():
        raise ValueError("The profiled analysis did not finish")
    a = np.loadtxt(job/"results/abaqus_load_cmod.csv", delimiter=",", comments="#")
    b = np.loadtxt(args.baseline/"results/abaqus_load_cmod.csv", delimiter=",", comments="#")
    if not np.array_equal(a,b):
        raise ValueError("Profiled response differs from the matched benchmark")
    hashes = {}
    for name in ["nodes.txt", "elements.txt", "top_nodes.txt", "left_nodes.txt",
                 "right_nodes.txt", "cmod1.txt", "cmod2.txt"]:
        path = job/"matlab_mesh"/name
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != hashlib.sha256((args.baseline/"matlab_mesh"/name).read_bytes()).hexdigest():
            raise ValueError("Profiled mesh or boundary set differs: "+name)
        hashes[name] = digest
    with (folder/"hotspots.csv").open(encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    rows = [row for row in rows if row["Process"]=="standard.exe"]
    assembly_names = {
        "SMAStaDirAssembledOperators::AssembleElements",
        "SMAEqsDirAssembledOperators::Assemble",
        "SMAEqsDirAssembledOperators::AssembleSupernode", "assemblekernel"}
    selected = [dict(function=row["Function"], module=row["Module"],
                     sampled_CPU_time_s=float(row["CPU Time"])) for row in rows
                if row["Function"] in assembly_names or row["Module"]=="standardU.dll"]
    user = sum(row["sampled_CPU_time_s"] for row in selected if row["module"]=="standardU.dll")
    assembly = sum(row["sampled_CPU_time_s"] for row in selected if row["function"] in assembly_names)
    msg = (job/"Gregoire_3PB.msg").read_text(errors="replace")
    solver = re.findall(r"SOLVER ELAPSED TIME:\s*([\d.Ee+-]+)\s*(ms|s)\b", msg)
    summary = dict(
        scope="One separate small/coarse CPU1 2,000-increment profile; sampling estimates, not benchmark timings.",
        response_arrays_exactly_equal=True, response_rows=len(a), mesh_sha256=hashes,
        user_library_self_sampled_CPU_time_s=user,
        explicitly_named_assembly_self_sampled_CPU_time_s=assembly,
        standard_process_total_sampled_CPU_time_s=sum(float(row["CPU Time"]) for row in rows),
        selected_self_samples=selected,
        solver_elapsed_time_s=sum(float(value)*(.001 if unit=="ms" else 1) for value,unit in solver),
        solver_passes=len(solver),
        limitations=["Self samples exclude time in callees; unknown symbols remain unallocated.",
                     "standardU.dll contains UMAT, helper routines and external-database initialization.",
                     "Named assembly self samples are a lower bound on identifiable assembly work, not a complete phase timer.",
                     "Sampled CPU-time estimates and Abaqus CPU/elapsed timers have different scopes and are not summed or rescaled.",
                     "The profiler reports missing symbols and a PulseEvent collection warning.",
                     "Other numerical validation jobs were active; this is not an isolated performance observation."])
    (folder/"analysis_summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
