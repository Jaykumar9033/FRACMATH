"""Profile only the native Standard process in a separate serial job.

Attaching after process startup excludes early initialization. The report
records its actual window; samples are not complete assembly wall timers.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import psutil

from run_scaling_study import setup, env_abq
from run_mesh_study import command_abaqus


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--source-snapshot',type=Path,required=True)
    parser.add_argument('--vtune',type=Path,default=Path(r'C:\Program Files (x86)\Intel\oneAPI\vtune\2025.0\bin64\vtune.exe'))
    args = parser.parse_args()
    folder = args.workspace.resolve()
    if folder.exists():
        raise ValueError('Use a new workspace for each collection')
    setup(folder,args.source_snapshot.resolve())
    pdb = str(folder/'standardU.pdb')
    (folder/'abaqus_v6.env').write_text(
        'compile_fortran += ["/names:lowercase", "/Zi"]\n'
        'link_sl += '+repr(' /DEBUG /PDB:"'+pdb+'"')+'\n')
    job = folder/'Gregoire_3PB'
    job.mkdir()
    shutil.copy2(folder/'abaqus_v6.env',job/'abaqus_v6.env')
    env = env_abq('small','coarse',2000,-.1,cpus=1)
    env['PSModulePath'] = str(Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/Modules')
    existing = {p.pid for p in psutil.process_iter(['name']) if (p.info['name'] or '').lower()=='standard.exe'}
    if existing:
        raise ValueError('Another Standard solve is active; run collections sequentially')
    with (folder/'run.log').open('w') as stream:
        application = subprocess.Popen(command_abaqus(folder),cwd=folder,env=env,stdout=stream,stderr=subprocess.STDOUT)
        started = time.monotonic()
        target = None
        while time.monotonic()-started < 180:
            children = psutil.Process(application.pid).children(recursive=True)
            candidates = [p for p in children if p.name().lower()=='standard.exe']
            if candidates:
                target = candidates[0]
                break
            if application.poll() is not None:
                raise RuntimeError('Abaqus exited before Standard started; inspect run.log')
            time.sleep(.2)
        if target is None:
            raise RuntimeError('No Standard process appeared within 180 seconds')
        result = folder/'vtune_result'
        command = [str(args.vtune),'-collect','hotspots','-knob','sampling-mode=sw',
                   '-knob','enable-stack-collection=true','-target-pid',str(target.pid),
                   '-result-dir',str(result)]
        sta = job/'Gregoire_3PB.sta'
        before = sta.read_text(errors='replace') if sta.exists() else ''
        record = dict(command=command,debug_symbols=True,
                      scope='Native Standard process only; samples after attach, excluding initial startup. Separate 2,000-increment serial solve.',
                      sta_before_attach=before,user_pdb_preserved=Path(pdb).exists())
        with (folder/'collection.log').open('w') as collector_log:
            collected = subprocess.run(command,cwd=folder,env=env,stdout=collector_log,stderr=subprocess.STDOUT)
        record['collection_return_code'] = collected.returncode
        record['application_return_code'] = application.wait()
    for report in ['summary','hotspots','callstacks']:
        options = [str(args.vtune),'-report',report,'-r',str(result),'-format','csv',
                   '-report-output',str(folder/(report+'.csv'))]
        if report=='hotspots':
            options += ['-group-by','process,function,module']
        with (folder/(report+'_export.log')).open('w') as stream:
            exported = subprocess.run(options,env=env,stdout=stream,stderr=subprocess.STDOUT)
        record[report+'_export_return_code'] = exported.returncode
    record['user_pdb_preserved'] = Path(pdb).exists()
    (folder/'profile_manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2),flush=True)
    if collected.returncode or record['application_return_code']:
        raise SystemExit('Collection or analysis failed; preserve and inspect the logs')


if __name__=='__main__':
    main()
