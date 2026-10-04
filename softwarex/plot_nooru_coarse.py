"""Check and plot the completed 25 mm-notch coarse pure-tension case."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    package = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, default=package/'reproducibility/nooru_25mm_coarse')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    output = args.output or args.case/'analysis'
    record = json.loads((args.case/'completion.json').read_text())
    mesh = json.loads((args.case/'mesh_metadata.json').read_text())
    if not record['completed'] or mesh['notch_depth_mm'] != 25 or mesh['notch_width_mm'] != 5:
        raise ValueError('Require the completed published-geometry case')
    history = np.loadtxt(args.case/'Job-1_gauge_results.csv', delimiter=',')
    targets = np.loadtxt(args.case/'accepted_targets.csv', delimiter=',')
    gauge = history[:, 2:6].mean(axis=1)
    error = float(np.max(np.abs(gauge-.2*targets[:, 0])))
    if (len(history) != len(targets) or not np.isfinite(history).all()
            or history[:, 6].max() > 1e-6 or error > 1e-8
            or abs(gauge[-1]-.2) > 1e-8 or np.any(np.diff(gauge) <= 0)):
        raise ValueError('Incomplete or unconverged gauge history')
    x = np.r_[0, gauge]
    y = np.r_[0, history[:, 1]]
    experiment = np.loadtxt(package/'reproducibility/experimental_3d/nooru_47_05_digitized.csv',
                            delimiter=',', skiprows=1)
    grid = np.linspace(0, min(x[-1], experiment[-1, 0]), 1001)
    difference = np.interp(grid, x, y)-np.interp(grid, experiment[:, 0], experiment[:, 1])
    summary = dict(elements=mesh['elements'], dofs=mesh['dofs'],
                   accepted_increments=len(history),
                   rejected_trials=int(np.loadtxt(args.case/'rejected_trial_count.csv')),
                   peak_N=float(y.max()), peak_gauge_mm=float(x[y.argmax()]),
                   experimental_peak_N=float(experiment[:, 1].max()),
                   peak_error_percent=float(100*(y.max()/experiment[:, 1].max()-1)),
                   curve_NRMSE_percent=float(100*np.sqrt(np.mean(difference**2))/experiment[:, 1].max()),
                   max_equilibrium_residual=float(history[:, 6].max()),
                   max_gauge_error_mm=error, final_mean_gauge_mm=float(gauge[-1]),
                   scope='One completed 25 mm-notch pure-tension mesh; digitized experimental data. No 3D mesh-convergence claim.')
    output.mkdir(parents=True, exist_ok=True)
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    plt.rcParams.update({'font.size': 11})
    fig, ax = plt.subplots(figsize=(6, 3.5), layout='constrained')
    ax.plot(experiment[:, 0], experiment[:, 1]/1000, 'o-', color='#333333', ms=3,
            lw=1.2, label='47-05 experiment (digitized)')
    ax.plot(x, y/1000, color='#4477AA', lw=1.7,
            label='MATLAB: 35,917 TET4 elements')
    ax.set(xlabel='Mean 65 mm gauge displacement (mm)', ylabel='Normal load (kN)',
           xlim=(0, .2), ylim=(0, 22))
    ax.grid(alpha=.2)
    ax.legend(fontsize=8)
    for extension in ['png', 'pdf']:
        fig.savefig(output/('nooru_tension_comparison.'+extension), dpi=300)
    plt.close(fig)
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
