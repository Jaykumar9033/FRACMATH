"""Plot measured medians and observed ranges for three timing observations."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    summary = json.loads(args.summary.read_text())
    baseline = json.loads(args.baseline.read_text())
    rows = summary['runs']
    if summary['observations'] != 3 or len(rows) != 30:
        raise ValueError('Require all 30 configurations with three observations')
    configs = ['matlab_cpu1', 'matlab_cpu8', 'matlab_gpu_hybrid', 'abaqus_cpu1', 'abaqus_cpu8']
    labels = ['MAT 1', 'MAT 8', 'MAT GPU', 'ABA 1', 'ABA 8']
    colors = ['#4477AA', '#66CCEE', '#228833', '#CC6677', '#AA3377']
    plt.rcParams.update({'font.size': 11})
    fig, axes = plt.subplots(3, 3, figsize=(11, 9.1), layout='constrained')
    table = [r'\begin{table}[htbp]', r'\centering\small',
             r'\caption{Size/mesh computing study: median time in seconds from three sequential observations per setting. MATLAB covers the load loop; Abaqus covers analysis and output. The observed ranges are shown in Figure~\ref{fig:timing}. GPU denotes the hybrid backend.}',
             r'\label{tab:scaling}', r'\begin{tabular}{llrrrrrr}', r'\hline',
             r'Size & Mesh & DOFs & MAT 1 & MAT 8 & MAT GPU & ABA 1 & ABA 8 \\', r'\hline']
    for i, size in enumerate(['small', 'large']):
        for j, mesh in enumerate(['coarse', 'medium', 'fine']):
            selected = [next(r for r in rows if (r['size'], r['mesh'], r['config']) == (size, mesh, c)) for c in configs]
            medians = np.array([r['median_s'] for r in selected])
            errors = np.array([[r['median_s']-r['minimum_s'] for r in selected],
                               [r['maximum_s']-r['median_s'] for r in selected]])
            ax = axes[i, j]
            ax.bar(labels, medians, yerr=errors, capsize=3, color=colors)
            ax.set(title=size.capitalize()+' / '+mesh, ylabel='Measured time (s)')
            ax.tick_params(axis='x', labelrotation=35)
            ax.grid(axis='y', alpha=.2)
            dofs = next(r['dofs'] for r in baseline['runs'] if (r['size'], r['mesh']) == (size, mesh))
            values = [('%.1f' if r['config'].startswith('matlab') else '%.0f') % r['median_s'] for r in selected]
            table.append(' & '.join([size.capitalize(), mesh, format(dofs, ','), *values])+r' \\')
    package = Path(__file__).resolve().parent
    profile = json.loads((package/'reproducibility/abaqus_profile/analysis_summary.json').read_text())
    names = ['User library', 'Named assembly']
    values = [profile['user_library_self_sampled_CPU_time_s'],
              profile['explicitly_named_assembly_self_sampled_CPU_time_s']]
    ax = axes[2, 0]
    bars = ax.bar(names, values, color=['#4477AA', '#CC6677'])
    ax.bar_label(bars, fmt='%.2f s', padding=3)
    ax.set(title='Separate Abaqus CPU1 profile', ylabel='Sampled CPU self time (s)', ylim=(0, 4.8))
    ax.tick_params(axis='x', labelrotation=15)
    ax.grid(axis='y', alpha=.2)
    axes[2, 1].axis('off')
    axes[2, 1].text(0, .95, 'User library: UMAT, helpers\nand initialization.\n\nAssembly: four named routines.\nCallees and unknown work excluded.\n\nNot complete phase wall timers.\nNot part of the 90 benchmark runs.',
                    va='top', fontsize=11, transform=axes[2, 1].transAxes)
    axes[2, 2].axis('off')
    table.extend([r'\hline', r'\end{tabular}', r'\end{table}'])
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'scaling_table.tex').write_text('\n'.join(table)+'\n', encoding='utf-8')
    fig.savefig(args.output/'scaling_timings.pdf')
    fig.savefig(args.output/'scaling_timings.png', dpi=220)
    plt.close(fig)


if __name__ == '__main__':
    main()
