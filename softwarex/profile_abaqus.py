"""Collect an optional, separate Abaqus user-mode CPU-sampling profile.

Requires Intel VTune. Profiling costs never enter the benchmark table.
The output records sampled CPU work, not assembly wall time.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from run_scaling_study import setup, env_abq
from run_mesh_study import command_abaqus


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--source-snapshot', type=Path, required=True)
    parser.add_argument('--vtune', type=Path, default=Path(r'C:\Program Files (x86)\Intel\oneAPI\vtune\2025.0\bin64\vtune.exe'))
    args = parser.parse_args()
    if not args.vtune.exists():
        raise FileNotFoundError('Intel VTune is not installed at the selected path')
    folder = args.workspace.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    result = folder / 'vtune_result'
    if result.exists():
        raise ValueError('Use a new workspace for each profile')
    setup(folder, args.source_snapshot.resolve())
    environment = env_abq('small', 'coarse', 2000, -0.1, cpus=1)
    command = [str(args.vtune), '-collect', 'hotspots', '-knob', 'sampling-mode=sw',
               '-knob', 'enable-stack-collection=true', '-result-dir', str(result),
               '-follow-child', '-app-working-dir', str(folder), '--'] + command_abaqus(folder)
    record = dict(command=command,
                  scope='Separate small/coarse CPU1 2,000-increment analysis; user-mode CPU sampling. Not wall-time attribution and not a benchmark observation.',
                  interpretation='UMAT-inclusive stacks may estimate material CPU work. Assembly is reported only if named symbols identify it; unknown solver symbols remain unallocated.')
    with (folder / 'collection.log').open('w', encoding='utf-8') as stream:
        process = subprocess.run(command, cwd=folder, env=environment, stdout=stream, stderr=subprocess.STDOUT)
    record['collection_return_code'] = process.returncode
    if process.returncode == 0:
        for report in ['summary', 'hotspots']:
            output = folder / (report + '.csv')
            options = [str(args.vtune), '-report', report, '-r', str(result), '-format', 'csv',
                       '-report-output', str(output)]
            if report == 'hotspots':
                options += ['-group-by', 'process,function,module']
            with (folder / (report + '_export.log')).open('w', encoding='utf-8') as stream:
                exported = subprocess.run(options, stdout=stream, stderr=subprocess.STDOUT)
            record[report + '_export_return_code'] = exported.returncode
    (folder / 'profile_manifest.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
