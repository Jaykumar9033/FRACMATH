"""Compare a full beginner-entry execution with the preserved 10,000-step state."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat


def main():
    package = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    folder = args.workspace.resolve()
    reference = package/"reproducibility/results_10000/verified_state.mat"
    result = folder/"student_results/verified_state.mat"
    old = loadmat(reference, simplify_cells=True)
    new = loadmat(result, simplify_cells=True)
    if len(new["F"]) != 10000:
        raise ValueError("Require the complete 10,000-step entry execution")
    comparisons = {}
    fields = ["nodes", "elems", "omega", "kappa", "u", "CMOD", "F", "RelRes"]
    for name in fields:
        a, b = np.asarray(old[name]), np.asarray(new[name])
        if a.shape != b.shape or not np.isfinite(b).all():
            raise ValueError("Invalid saved array: "+name)
        comparisons[name] = dict(exactly_equal=bool(np.array_equal(a,b)),
                                maximum_absolute_difference=float(np.max(np.abs(a-b))))
    for snapshot in ["snap_peak", "snap_pp"]:
        for name in ["u", "omega", "load"]:
            a, b = np.asarray(old[snapshot][name]), np.asarray(new[snapshot][name])
            comparisons[snapshot+"."+name] = dict(
                exactly_equal=bool(np.array_equal(a,b)),
                maximum_absolute_difference=float(np.max(np.abs(a-b))))
    original = (package/"start_here.m").read_text(encoding="utf-8")
    tested = (folder/"start_here.m").read_text(encoding="utf-8")

    def executable_lines(text):
        rows = []
        for line in text.splitlines():
            if line.lstrip().startswith("%"):
                continue
            line = line.strip()
            if line:
                rows.append(" ".join(line.split()))
        return rows

    expected = executable_lines(original.replace("show_figures = true;", "show_figures = false;"))
    observed = executable_lines(tested)
    if observed != expected:
        raise ValueError("Tested entry differs beyond comments, whitespace and the documented graphics option")
    report = dict(steps=10000, comparisons=comparisons,
                  all_numerical_arrays_exactly_equal=all(row["exactly_equal"] for row in comparisons.values()),
                  graphics="Disabled only for the headless check; numerical settings unchanged.",
                  original_entry_sha256=hashlib.sha256((package/"start_here.m").read_bytes()).hexdigest(),
                  tested_entry_sha256=hashlib.sha256((folder/"start_here.m").read_bytes()).hexdigest(),
                  reference_state_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),
                  tested_state_sha256=hashlib.sha256(result.read_bytes()).hexdigest(),
                  timing_scope="Numerical verification with other validation jobs active; not a benchmark observation.")
    (folder/"comparison.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))
    if not report["all_numerical_arrays_exactly_equal"]:
        raise SystemExit("The entry does not exactly reproduce the preserved numerical state")


if __name__ == "__main__":
    main()
