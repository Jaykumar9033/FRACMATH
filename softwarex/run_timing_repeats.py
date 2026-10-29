"""Run two additional observations of the 30 matched configurations.

Example: python softwarex/run_timing_repeats.py --baseline C:/runs/scaling --workspace C:/runs/repeats
Runs are sequential, use the exact baseline meshes, and never overwrite them.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from run_scaling_study import SIZES, MESHES, CONFIGS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--workspace', required=True, type=Path)
    args = parser.parse_args()
    baseline = args.baseline.resolve()
    workspace = args.workspace.resolve()
    if baseline == workspace or baseline in workspace.parents:
        raise ValueError('Use a repeat workspace outside the baseline')
    scripts = Path(__file__).resolve().parent
    baseline_summary = json.loads((baseline / 'analysis/summary.json').read_text())
    if baseline_summary['completed'] != 30 or len(baseline_summary['runs']) != 30:
        raise ValueError('The baseline must contain all 30 configurations')
    for repeat in [2, 3]:
        target = workspace / ('observation_%d' % repeat)
        target.mkdir(parents=True, exist_ok=True)
        for size in SIZES:
            for mesh in MESHES:
                common = target / size / mesh / 'common/Gregoire_3PB/matlab_mesh'
                if not common.exists():
                    shutil.copytree(baseline / size / mesh / 'common/Gregoire_3PB/matlab_mesh', common)
        # Reverse the configuration order in the third observation.
        order = list(CONFIGS)
        if repeat == 3:
            order.reverse()
        command = [sys.executable, str(scripts / 'run_scaling_study.py'),
                   '--workspace', str(target), '--stage', 'solve', '--configs'] + order
        print('Observation', repeat, 'configuration order:', order, flush=True)
        subprocess.run(command, check=True)
        subprocess.run([sys.executable, str(scripts / 'analyze_scaling_study.py'),
                        '--workspace', str(target), '--output', str(target / 'analysis')], check=True)
    subprocess.run([sys.executable, str(scripts / 'analyze_timing_repeats.py'),
                    '--baseline', str(baseline), '--workspace', str(workspace)], check=True)


if __name__ == '__main__':
    main()
