"""Export the manuscript timing table from the three saved observations.

No simulations are run. Each entry is the median and observed min-max range.
Use --check-manuscript to compare the exported table with a LaTeX manuscript.
"""
import argparse
import json
from pathlib import Path
import re
import statistics

PACKAGE = Path(__file__).resolve().parent
CONFIGS = ("matlab_cpu1", "matlab_cpu8", "matlab_gpu_hybrid",
           "abaqus_cpu1", "abaqus_cpu8")


def make_table(summary, baseline):
    if summary["observations"] != 3 or len(summary["runs"]) != 30:
        raise ValueError("Require 30 configurations with three observations each.")
    rows = {}
    for row in summary["runs"]:
        key = (row["size"], row["mesh"], row["config"])
        if key in rows:
            raise ValueError("Duplicate configuration: " + str(key))
        observations = [row["time_%d_s" % i] for i in (1, 2, 3)]
        if not all(value > 0 for value in observations):
            raise ValueError("Invalid timing observation.")
        expected = (statistics.median(observations), min(observations), max(observations))
        actual = (row["median_s"], row["minimum_s"], row["maximum_s"])
        if actual != expected:
            raise ValueError("Summary does not match the recorded observations.")
        rows[key] = row
    lines = [
        r"\begin{table}[!htbp]", r"\centering\small",
        r"\setlength{\tabcolsep}{3pt}", r"\renewcommand{\arraystretch}{1.12}",
        r"\begin{tabular}{@{}llrrrrrr@{}}", r"\toprule",
        r"& & & \multicolumn{3}{c}{MATLAB} & \multicolumn{2}{c}{Abaqus} \\",
        r"\cmidrule(lr){4-6}\cmidrule(lr){7-8}",
        r"Size & Mesh & DOFs & CPU1 & CPU8 & Hybrid GPU & CPU1 & CPU8 \\",
        r"\midrule",
    ]
    for size in ("small", "large"):
        for mesh in ("coarse", "medium", "fine"):
            dofs = {r["dofs"] for r in baseline["runs"]
                    if (r["size"], r["mesh"]) == (size, mesh)}
            if len(dofs) != 1:
                raise ValueError("Missing or inconsistent DOF count.")
            cells = [size.capitalize(), mesh, format(dofs.pop(), ",")]
            for config in CONFIGS:
                row = rows[size, mesh, config]
                precision = ".1f" if config.startswith("matlab") else ".0f"
                values = [format(row[field], precision)
                          for field in ("median_s", "minimum_s", "maximum_s")]
                cells.append(r"\shortstack[r]{" + values[0] + r"\\("
                             + values[1] + "-" + values[2] + ")}")
            lines.append(" & ".join(cells) + r" \\[3pt]")
        if size == "small":
            lines.append(r"\midrule")
    lines.extend([
        r"\bottomrule", r"\end{tabular}",
        r"\caption{Measured times in seconds for the five computing configurations. Each entry gives the median, with the observed minimum-maximum range in parentheses, from three runs. CPU1 and CPU8 denote one and eight computational threads; GPU denotes the hybrid CPU-GPU implementation. MATLAB times cover all loading increments, and Abaqus times cover analysis and output. The ranges are not confidence intervals. This study uses its own increment controls and is separate from the matched fixed-increment comparisons in Table~\ref{tab:fixed-timing}. Differences in timing scope and equilibrium procedures prevent a direct ranking of program speed.}",
        r"\label{tab:scaling}", r"\end{table}",
    ])
    return "\n".join(lines) + "\n"


def manuscript_table(text):
    marker = r"\label{tab:scaling}"
    index = text.index(marker)
    start = text.rfind(r"\begin{table}", 0, index)
    end = text.index(r"\end{table}", index) + len(r"\end{table}")
    if start < 0:
        raise ValueError("Timing table environment not found.")
    return text[start:end]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path,
                        default=PACKAGE / "reproducibility/timing_repeats/analysis/summary.json")
    parser.add_argument("--baseline", type=Path,
                        default=PACKAGE / "reproducibility/scaling_study/analysis/summary.json")
    parser.add_argument("--output", type=Path, default=PACKAGE / "tables/scaling_table.tex")
    parser.add_argument("--check-manuscript", type=Path)
    args = parser.parse_args()
    result = make_table(json.loads(args.summary.read_text()), json.loads(args.baseline.read_text()))
    if args.check_manuscript:
        actual = manuscript_table(args.check_manuscript.read_text(encoding="utf-8-sig"))
        if re.sub(r"\s+", "", result) != re.sub(r"\s+", "", actual):
            raise SystemExit("The manuscript timing table differs from the saved observations.")
        print("All 30 median/range entries match the manuscript.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result, encoding="utf-8")
    print("Saved " + str(args.output))


if __name__ == "__main__":
    main()
