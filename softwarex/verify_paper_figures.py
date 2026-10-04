"""Rebuild every generated manuscript figure in a separate workspace.

PNG files are compared by pixels. PDFs are rendered by pdftoppm and their
pixels compared, so timestamps do not cause false failures. Supplied
geometry illustrations are checked against their archived source images.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    folder = args.workspace.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    commands = [
        ['plot_verified_figures.py', '--output', str(folder)],
        ['rebuild_3d_figures.py', '--output', str(folder)],
        ['plot_timing_repeats.py', '--summary', str(package/'reproducibility/timing_repeats/analysis/summary.json'),
         '--baseline', str(package/'reproducibility/scaling_study/analysis/summary.json'), '--output', str(folder)],
        ['analyze_mesh_study.py', '--output', str(folder/'mesh_report'), '--figures', str(folder)],
        ['analyze_nooru_mesh_study.py', '--workspace', str(package/'reproducibility/nooru_25mm_mesh_study'),
         '--require-all', '--output', str(folder/'nooru_report')],
    ]
    for index, command in enumerate(commands, 1):
        with (folder/('command_%d.log' % index)).open('w') as stream:
            subprocess.run([sys.executable, str(package/command[0]), *command[1:]],
                           stdout=stream, stderr=subprocess.STDOUT, check=True)
    generated = {
        'fig_mesh.png': 'fig_mesh.png',
        'load_cmod_verified.png': 'load_cmod_verified.png',
        'damage_verified.png': 'damage_verified.png',
        'scaling_timings.pdf': 'scaling_timings.pdf',
        'nooru_tension_comparison.pdf': 'nooru_report/nooru_tension_mesh_comparison.pdf',
        'nooru_damage_evolution_shared_bar.png': 'nooru_damage_evolution_shared_bar.png',
        'torsion_damage_evolution_shared_bar.png': 'torsion_damage_evolution_shared_bar.png',
        'mesh_study_overview.pdf': 'mesh_study_overview.pdf',
    }
    checks = []
    for name, regenerated in generated.items():
        original = package/'figures'/name
        rebuilt = folder/regenerated
        if original.suffix == '.pdf':
            raster_files = []
            for label, pdf in [('original', original), ('rebuilt', rebuilt)]:
                output = folder/(original.stem+'_'+label)
                subprocess.run(['pdftoppm', '-singlefile', '-r', '100', '-png', str(pdf), str(output)], check=True)
                raster_files.append(output.with_suffix('.png'))
            original, rebuilt = raster_files
        left = np.asarray(Image.open(original).convert('RGBA'))
        right = np.asarray(Image.open(rebuilt).convert('RGBA'))
        same_shape = left.shape == right.shape
        checks.append(dict(asset=name, identical_pixels=bool(same_shape and np.array_equal(left, right)),
                           shape_matches=same_shape))
    for name in ['nooru_BC_2D.png', 'torsion.png']:
        original = package/'figures'/name
        source = package/'figure_sources/static'/name
        checks.append(dict(asset=name, identical_archived_source_bytes=
                           hashlib.sha256(original.read_bytes()).digest()==hashlib.sha256(source.read_bytes()).digest(),
                           scope='Supplied geometry illustration; not a numerical response plot.'))
    passed = all(row.get('identical_pixels', row.get('identical_archived_source_bytes')) for row in checks)
    report = dict(passed=passed, assets=checks, manuscript_figures=6,
                  scope='Archive-backed figure reproduction. Numerical solver verification and licensed full reruns are separate checks.')
    (folder/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit('A figure differs from its archived-data reconstruction')


if __name__ == '__main__':
    main()
