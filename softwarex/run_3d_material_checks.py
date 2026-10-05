"""Check the actual TET4 material routines without a structural solve.

Requires MATLAB. Functions are extracted unchanged from the supplied source,
so the tests exercise its formulas rather than a second implementation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--source',type=Path)
    args = parser.parse_args()
    package = Path(__file__).resolve().parent
    source = args.source or package / 'reproducibility/experimental_3d/source/damage_static.m'
    text = source.read_text(encoding='utf-8')
    blocks = re.split(r'(?m)(?=^function )', text)
    names = ['material_scale', 'precompute_TET4_vectorized', 'oliver_bandwidth_TET4',
             'eqv_strain_modified_vm_vec', 'max_principal_strain_direction_vec']
    functions = []
    for name in names:
        block = next(block for block in blocks if re.search(r'\b' + name + r'\(', block.split('\n')[0]))
        functions.append(block)
    args.workspace.mkdir(parents=True, exist_ok=True)
    driver = (package / 'material_checks_3d.m').read_text(encoding='utf-8')
    state_history='history_old.omega' in text
    if state_history:
        driver=driver.replace('history_for = @(kappa,omega) kappa;',
                              "history_for = @(kappa,omega) struct('kappa',kappa,'omega',omega);")
        driver=driver.replace('check_rotating_history = false;', 'check_rotating_history = true;')
    (args.workspace / 'material_checks_3d.m').write_text(driver + '\n' + '\n'.join(functions), encoding='utf-8')
    (args.workspace / 'source_manifest.json').write_text(json.dumps(dict(
        source=str(source.resolve()), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        functions=names, retains_damage_history=state_history,
        scope='Local TET4 mapping, direction, projected width, finite-interval softening integral and unloading checks; rotating-direction irreversibility additionally checked for state-history source. Not structural mesh convergence.'), indent=2), encoding='utf-8')
    with (args.workspace / 'console.log').open('w', encoding='utf-8') as stream:
        subprocess.run(['matlab', '-batch', 'material_checks_3d'], cwd=args.workspace,
                       stdout=stream, stderr=subprocess.STDOUT, check=True)


if __name__ == '__main__':
    main()
