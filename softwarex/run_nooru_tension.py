"""Run the local-gauge-controlled Nooru-Mohamed pure-tension comparison.

Requires licensed MATLAB. Example:
python softwarex/run_nooru_tension.py --workspace C:/runs/nooru_tension
"""
import argparse
from pathlib import Path
import shutil
import subprocess
import time
import json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--steps', nargs='+', type=int, default=[600])
    args = parser.parse_args()
    data = Path(__file__).resolve().parent / 'reproducibility/experimental_3d'
    args.workspace.mkdir(parents=True, exist_ok=True)
    for steps in args.steps:
        folder = args.workspace / ('steps_%d' % steps)
        folder.mkdir(exist_ok=True)
        for source in (data / 'source').iterdir():
            shutil.copy2(source, folder / source.name)
        shutil.copy2(data / 'gauge_triplets.csv', folder / 'gauge_triplets.csv')
        script = """a=readmatrix('gauge_triplets.csv'); G=sparse(a(:,1),a(:,2),a(:,3),4,11799);
setenv('OMP_NUM_THREADS','1'); maxNumCompThreads(1);
opts=struct('load_path','tension','nIncr',%d,'Uy_end',0.2,'show_live',false,'save_all_increment_geometry',false,'show_mesh',false,'save_show_mesh',false,'print_stride',20,'maxIter',150,'use_line_search',true,'tol',1e-6,'strict_equilibrium',true,'gauge_control',true,'maxLineSearch',12,'gauge_matrix',G,'out_dir',pwd);
damage_static('Job-1',opts);
""" % steps
        (folder / 'run_case.m').write_text(script, encoding='utf-8')
        start = time.perf_counter()
        with (folder / 'console.log').open('w', encoding='utf-8') as stream:
            subprocess.run(['matlab', '-batch', 'run_case'], cwd=folder,
                           stdout=stream, stderr=subprocess.STDOUT, check=True)
        (folder / 'run_manifest.json').write_text(json.dumps({
            'steps': steps, 'target_mean_local_gauge_mm': 0.2,
            'wall_s': time.perf_counter() - start,
            'material': {'E_MPa': 29000, 'nu': 0.2, 'ft_MPa': 3, 'Gf_N_per_mm': 0.11},
            'control': 'mean of four 65 mm vertical gauges',
            'threads': 1}, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
