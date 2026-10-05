"""Summarize measured MATLAB and Abaqus costs without inventing UMAT timings.

Run from the repository root: python softwarex/compare_solver_diagnostics.py
Optional arguments: MATLAB timing file, Abaqus .msg file, output JSON file.
"""
import json
import re
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
DEFAULT_MATLAB = PACKAGE / "reproducibility/results_10000/matlab_timing.txt"
DEFAULT_MSG = PACKAGE / "reproducibility/abaqus/Gregoire_3PB/diagnostics/Gregoire_3PB.msg"
DEFAULT_OUTPUT = PACKAGE / "reproducibility/solver_diagnostics.json"


def required_float(pattern, text, label):
    match = re.search(pattern, text, re.I)
    if not match:
        raise ValueError("Missing %s" % label)
    return float(match.group(1))


def summarize(matlab_path, msg_path):
    matlab = Path(matlab_path).read_text(encoding="utf-8", errors="replace")
    msg = Path(msg_path).read_text(encoding="utf-8", errors="replace")
    mt = required_float(r"Solver wall-clock:\s*([\d.]+)\s*s", matlab, "MATLAB wall time")
    at = required_float(r"WALLCLOCK TIME\s*\(SEC\)\s*=\s*([\d.Ee+-]+)", msg, "Abaqus wall time")
    costs = {}
    for label, pattern in {
        "assembly": r"assembly:\s*([\d.]+)\s*s",
        "factorization": r"factorization:\s*([\d.]+)\s*s",
        "damage": r"damage:\s*([\d.]+)\s*s",
        "solve": r"solve:\s*([\d.]+)\s*s",
    }.items():
        costs[label] = required_float(pattern, matlab, "MATLAB " + label)
    entries = re.findall(r"SOLVER ELAPSED TIME:\s*([\d.Ee+-]+)\s*(ms|s)\b", msg, re.I)
    solver_seconds = [float(value) * (0.001 if unit.lower() == "ms" else 1)
                      for value, unit in entries]
    if not solver_seconds:
        raise ValueError("No Abaqus per-pass solver times found")
    def count(pattern, label):
        return int(required_float(pattern, msg, label))
    passes = count(r"(\d+)\s+PASSES THROUGH THE EQUATION SOLVER", "Abaqus passes")
    if len(solver_seconds) != passes:
        raise ValueError("Solver timing entries (%d) differ from reported passes (%d)" %
                         (len(solver_seconds), passes))
    return {
        "matlab": {
            "wall_s": mt,
            "steps": int(required_float(r"Load steps:\s*(\d+)", matlab, "MATLAB steps")),
            "component_s": costs,
            "unattributed_s": round(mt - sum(costs.values()), 4),
        },
        "abaqus": {
            "wall_s": at,
            "accepted_increments": count(r"TOTAL OF\s+(\d+)\s+INCREMENTS", "Abaqus increments"),
            "alternate_force_tolerance_acceptances": len(re.findall(r"FORCE EQUILIBRIUM ACCEPTED USING THE ALTERNATE TOLERANCE", msg, re.I)),
            "cutbacks": count(r"(\d+)\s+CUTBACKS IN AUTOMATIC INCREMENTATION", "Abaqus cutbacks"),
            "solver_passes": passes,
            "factorizations": count(r"(\d+)\s+INVOLVE MATRIX DECOMPOSITION", "Abaqus factorizations"),
            "solver_time_entries": len(solver_seconds),
            "summed_solver_elapsed_s": round(sum(solver_seconds), 4),
            "remaining_wall_s": round(at - sum(solver_seconds), 4),
        },
        "interpretation": "Remaining Abaqus wall time combines UMAT, assembly, convergence, output, and overhead; the .msg file does not isolate these components. MATLAB and Abaqus use different increment histories, so wall times are not a speed ranking.",
    }


if __name__ == "__main__":
    paths = [Path(p) for p in sys.argv[1:]]
    if len(paths) > 3:
        raise SystemExit("Usage: compare_solver_diagnostics.py [MATLAB_TIMING] [ABAQUS_MSG] [OUTPUT_JSON]")
    defaults = [DEFAULT_MATLAB, DEFAULT_MSG, DEFAULT_OUTPUT]
    matlab_path, msg_path, output = paths + defaults[len(paths):]
    result = summarize(matlab_path, msg_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
