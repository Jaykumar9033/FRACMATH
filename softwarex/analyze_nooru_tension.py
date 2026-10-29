"""Compare converged 3D histories with the digitized experimental curve."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--steps', nargs='+', type=int, default=[600])
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    data = package / 'reproducibility/experimental_3d'
    exp = np.loadtxt(data / 'nooru_47_05_digitized.csv', delimiter=',', skiprows=1)
    fig, ax = plt.subplots(figsize=(6, 3.5), layout='constrained')
    ax.plot(exp[:, 0], exp[:, 1]/1000, 'ko-', ms=3, lw=1, label='47-05 experiment (digitized)')
    summary = {'experimental_peak_N': float(exp[:, 1].max()), 'runs': []}
    for steps in args.steps:
        a = np.loadtxt(args.workspace / ('steps_%d' % steps) / 'Job-1_gauge_results.csv', delimiter=',')
        if len(a) != steps or not np.isfinite(a).all() or a[:, 6].max() > 1e-6:
            raise ValueError('Incomplete or unconverged history: %d' % steps)
        x = a[:, 2:6].mean(axis=1)
        target = np.arange(1, steps+1)*0.2/steps
        if np.max(np.abs(x-target)) > 1e-8:
            raise ValueError('Gauge constraint failed')
        x = np.r_[0, x]; y = np.r_[0, a[:, 1]]
        grid = np.linspace(0, min(x[-1], exp[-1, 0]), 1001)
        error = np.interp(grid, x, y)-np.interp(grid, exp[:, 0], exp[:, 1])
        peak = int(np.argmax(y))
        summary['runs'].append({'steps': steps, 'peak_N': float(y[peak]),
            'peak_gauge_mm': float(x[peak]),
            'peak_error_percent': float(100*(y[peak]/exp[:, 1].max()-1)),
            'curve_NRMSE_percent_of_experimental_peak': float(100*np.sqrt(np.mean(error**2))/exp[:, 1].max()),
            'max_equilibrium_residual': float(a[:, 6].max()),
            'max_gauge_constraint_error_mm': float(np.max(np.abs(x[1:]-target)))})
        ax.plot(x, y/1000, lw=1.4, label='MATLAB: %d increments' % steps)
    p = [a['peak_N'] for a in summary['runs']]
    summary['peak_increment_sensitivity_percent'] = 100*abs(p[-1]-p[0])/p[-1] if len(p)>1 else None
    summary['rejected_runs'] = [{'steps': 300, 'failed_increment': 14, 'relative_residual': 0.01430, 'excluded': True}, {'steps': 1200, 'failed_increment': 55, 'relative_residual': 0.004185, 'excluded': True}]
    summary['scope'] = 'One nominal mesh; existing material parameters without fitting; idealized two-platen pure tension. Not a torsion or mixed-mode validation.'
    (data / 'comparison.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    ax.set(xlabel='Mean 65 mm gauge displacement (mm)', ylabel='Normal load (kN)', xlim=(0, 0.2), ylim=(0, 25))
    ax.grid(alpha=0.2); ax.legend(fontsize=8)
    for suffix in ['png', 'pdf']:
        fig.savefig(package / 'figures' / ('nooru_tension_comparison.'+suffix), dpi=300)
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
