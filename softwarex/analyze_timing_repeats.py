"""Compare three observations without treating timings as exact outputs."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--workspace', required=True, type=Path)
    args = parser.parse_args()
    folders = [args.baseline, args.workspace / 'observation_2', args.workspace / 'observation_3']
    summaries = [json.loads((folder / 'analysis/summary.json').read_text()) for folder in folders]
    for summary in summaries:
        if summary['completed'] != 30 or not all(row['hardware_response_check'] for row in summary['runs']):
            raise ValueError('Require three complete, response-checked studies')
    rows = []
    for reference in summaries[0]['runs']:
        size, mesh, config = (reference[key] for key in ['size', 'mesh', 'config'])
        observations = [next(row for row in summary['runs']
                             if (row['size'], row['mesh'], row['config']) == (size, mesh, config))
                        for summary in summaries]
        row = dict(size=size, mesh=mesh, config=config, observations=3)
        times = [item['wall_s'] for item in observations]
        row.update(time_1_s=times[0], time_2_s=times[1], time_3_s=times[2],
                   median_s=float(np.median(times)), minimum_s=min(times), maximum_s=max(times))
        state_paths = [folder / size / mesh / config for folder in folders]
        if config.startswith('matlab'):
            states = [loadmat(path / 'results/verified_state.mat', simplify_cells=True) for path in state_paths]
            fields = ['nodes', 'elems', 'u', 'omega', 'kappa', 'CMOD', 'F', 'RelRes',
                      'ExternalWork', 'ElasticEnergy', 'DamageDissipation']
            row['all_saved_numerical_arrays_exact'] = all(
                np.array_equal(states[0][field], state[field])
                for state in states[1:] for field in fields)
            row['max_load_difference_fraction'] = max(
                float(np.max(np.abs(state['F']-states[0]['F']))/np.max(states[0]['F']))
                for state in states[1:])
            row['max_final_damage_difference'] = max(
                float(np.max(np.abs(state['omega']-states[0]['omega']))) for state in states[1:])
            row['repeat_response_check'] = (row['max_load_difference_fraction'] <= 1e-3
                                            and row['max_final_damage_difference'] <= 1e-4)
        else:
            files = [path / 'Gregoire_3PB/results/abaqus_load_cmod.csv' for path in state_paths]
            curves = [np.loadtxt(path, delimiter=',', comments='#') for path in files]
            row['all_saved_response_arrays_exact'] = all(np.array_equal(curves[0], curve) for curve in curves[1:])
            grid = np.linspace(max(curve[0, 0] for curve in curves), min(curve[-1, 0] for curve in curves), 1001)
            if any(np.any(np.diff(curve[:, 0]) < -1e-8) for curve in curves):
                raise ValueError('A non-monotone response needs branch-aware comparison')
            base = np.interp(grid, curves[0][:, 0], curves[0][:, 1])
            row['max_load_difference_fraction'] = max(
                float(np.max(np.abs(np.interp(grid, curve[:, 0], curve[:, 1])-base))/curves[0][:, 1].max())
                for curve in curves[1:])
            row['repeat_response_check'] = row['max_load_difference_fraction'] <= 1e-3
            row['same_iteration_counts'] = all(
                all(item[key] == observations[0][key] for key in ['accepted_increments', 'solver_passes'])
                for item in observations[1:])
        if not row['repeat_response_check']:
            raise ValueError('Repeat response failed: %s/%s/%s' % (size, mesh, config))
        row['source_manifests'] = [hashlib.sha256((folder / 'manifest.json').read_bytes()).hexdigest() for folder in folders]
        rows.append(row)
    output = args.workspace / 'analysis'
    output.mkdir(exist_ok=True)
    (output / 'summary.json').write_text(json.dumps(dict(runs=rows, observations=3,
        scope='Three sequential workstation observations; median and observed range, not a confidence interval.'), indent=2), encoding='utf-8')
    keys = ['size', 'mesh', 'config', 'observations', 'time_1_s', 'time_2_s', 'time_3_s', 'median_s', 'minimum_s', 'maximum_s', 'repeat_response_check']
    with (output / 'timings.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=keys, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    print('All 30 configurations have three complete, response-checked observations.')


if __name__ == '__main__':
    main()
