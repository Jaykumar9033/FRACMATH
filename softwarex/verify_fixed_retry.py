"""Verify matched smaller-increment results and plot saved response histories.

python softwarex/verify_fixed_retry.py --workspace C:/runs/fixed_retry --output C:/runs/retry_check
Only saved files are read. No MATLAB or Abaqus numerical analysis is started.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from run_comparison_extension import validate_frozen_inputs
from analyze_comparison_extension import matlab_check, abaqus_check, comparison
from compare_solver_diagnostics import summarize


def verify(workspace, output):
    plan = json.loads((workspace / 'plan.json').read_text())
    validate_frozen_inputs(workspace, plan)
    report = {'frozen_inputs_verified': True, 'cases': {},
              'scope': 'Matched fixed schedules, distinct nonlinear algorithms; no adaptive replacement.'}
    curves = {}
    for name in ('baseline', 'coarse'):
        folder = workspace / name
        settings = plan['cases'][name]
        job = folder / 'Gregoire_3PB'
        mat, mc = matlab_check(folder / 'reference_matlab_oliver', job / 'matlab_mesh',
                               settings, 'oliver', 'modified_mises')
        result = {'matlab': mat, 'timing': summarize(
            folder / 'reference_matlab_oliver/matlab_timing.txt', job / 'Gregoire_3PB.msg')}
        if name == 'coarse':
            abq, ac = abaqus_check(job, settings)
            result.update(abaqus=abq, response=comparison(mc, ac))
            result['matlab_peak_excess_percent_relative_to_abaqus'] = 100 * (mat['peak_load_N'] / abq['peak_load_N'] - 1)
        else:
            h = np.genfromtxt(folder / 'failure_verified/abaqus_schedule.csv', delimiter=',', names=True)
            if not all(np.isfinite(h[field]).all() for field in h.dtype.names):
                raise ValueError('Non-finite baseline partial history')
            if abs(h['normalized_time'][0]) > 1.e-9:
                raise ValueError('Expected initial zero history row')
            accepted = len(h) - 1
            if not np.allclose(h['normalized_time'][1:], np.arange(1, accepted + 1) / settings['steps'], atol=1.e-7, rtol=0):
                raise ValueError('Partial baseline times differ from fixed schedule')
            expected_u = settings['final_displacement_mm'] * np.arange(len(h)) / settings['steps']
            displacement_tolerance = max(1.e-8, abs(settings['final_displacement_mm']) * 2.e-7)
            if not np.allclose(h['displacement_mm'], expected_u, atol=displacement_tolerance, rtol=0):
                raise ValueError('Partial baseline displacement differs from schedule')
            message = (job / 'Gregoire_3PB.msg').read_text()
            if 'FIXED TIME INCREMENT IS TOO LARGE' not in message:
                raise ValueError('Expected preserved convergence failure')
            ac = np.column_stack((h['cmod_mm'], h['load_N']))
            result['abaqus'] = {'completed': False, 'accepted_fixed_increments': accepted,
                'requested_fixed_increments': settings['steps'], 'finite_partial_history': True,
                'actual_fixed_schedule_verified': True,
                'maximum_displacement_error_mm': float(np.max(np.abs(h['displacement_mm'] - expected_u))),
                'displacement_tolerance_mm': displacement_tolerance,
                'last_converged_normalized_time': float(h['normalized_time'][-1]),
                'last_converged_displacement_mm': float(h['displacement_mm'][-1]),
                'last_converged_cmod_mm': float(h['cmod_mm'][-1]),
                'last_converged_load_N': float(h['load_N'][-1]),
                'reported_failed_increment_attempt': result['timing']['abaqus']['reported_increments'],
                'reason': 'Message file reports divergence followed by FIXED TIME INCREMENT IS TOO LARGE.',
                'adaptive_replacement': False}
            result['partial_response'] = comparison(mc[:accepted], ac[1:])
            mc = mc[:accepted]
        report['cases'][name] = result
        curves[name] = (mc, ac)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    figure, axes = plt.subplots(1, 2, figsize=(10.5, 4.1), layout='constrained')
    for axis, name in zip(axes, ('coarse', 'baseline')):
        mc, ac = curves[name]
        axis.plot(mc[:, 0], mc[:, 1] / 1000, color='#2166a5', label='MATLAB')
        axis.plot(ac[:, 0], ac[:, 1] / 1000, '--', color='#cc503e', label='Abaqus/UMAT')
        axis.set(xlabel='CMOD [mm]', ylabel='Load [kN]', xlim=(0, None), ylim=(0, None))
        axis.set_title('Coarse: completed 4,000 fixed increments' if name == 'coarse'
                       else 'Baseline: converged portion only')
        axis.spines[['top', 'right']].set_visible(False)
        axis.grid(alpha=.2)
        axis.legend(frameon=False)
    for suffix in ('png', 'pdf'):
        figure.savefig(output / ('retry_responses.' + suffix), dpi=240)
    plt.close(figure)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.workspace, args.output), indent=2))
