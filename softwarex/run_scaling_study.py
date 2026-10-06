"""Sequential 30-case 3PB hardware/size/mesh study.

python softwarex/run_scaling_study.py --workspace C:/runs/scaling
Use --pilot for five short correctness checks before the full study.
Each solve starts in a fresh process. A completed result is never overwritten.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone
from run_mesh_study import launch, command_abaqus, MATLAB_SOURCE, ABAQUS_SOURCE

ROOT = Path(__file__).resolve().parents[1]
SIZES = {'small': 1.0, 'large': 2.0}
# Absolute seeds stay fixed between sizes, so large specimens also have more DOFs.
MESHES = {'coarse': 2.0, 'medium': 1.0, 'fine': 0.75}
CONFIGS = {'matlab_cpu1': (1, 'cpu'), 'matlab_cpu8': (8, 'cpu'),
           'matlab_gpu_hybrid': (1, 'gpu_hybrid'),
           'abaqus_cpu1': (1, None), 'abaqus_cpu8': (8, None)}

def setup(folder, snapshot):
    folder.mkdir(parents=True, exist_ok=True)
    for name in ['run_3pb_abaqus_OLIVER_T3_FAST.py', 'cdm_umat_2d_OLIVER_T3_FAST.for']:
        shutil.copy2(snapshot / name, folder / name)
    (folder / 'abaqus_v6.env').write_text('compile_fortran += ["/names:lowercase"]\n')

def env_abq(size, mesh, steps, displacement, cpus=1, build=False):
    env = os.environ.copy()
    env.update(ABQ_SIZE_SCALE=str(SIZES[size]), ABQ_MESH_SCALE=str(MESHES[mesh]),
               ABQ_STUDY_BC='1', ABQ_U_FINAL=str(displacement*SIZES[size]),
               ABQ_N_INC=str(steps), ABQ_CPUS=str(cpus), ABQ_AUTO_PLOT='0',
               ABQ_BUILD_ONLY='1' if build else '0',
               ABQ_FIELD_FREQ=str(max(1, steps//20)),
               ABQ_INCREMENT_MODE='adaptive', ABQ_EXTRACT_ONLY='0')
    env['ABQ_EQ_LIMIT'] = '80' if size == 'large' and mesh in ['medium','fine'] else '0'
    return env

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--pilot', action='store_true')
    parser.add_argument('--stage', choices=['build', 'solve', 'all'], default='all')
    parser.add_argument('--sizes', nargs='+', choices=list(SIZES), default=list(SIZES))
    parser.add_argument('--meshes', nargs='+', choices=list(MESHES), default=list(MESHES))
    parser.add_argument('--configs', nargs='+', choices=list(CONFIGS), default=list(CONFIGS))
    args = parser.parse_args()
    args.workspace = args.workspace.resolve()
    args.workspace.mkdir(parents=True, exist_ok=True)
    steps, displacement = (200, -0.03) if args.pilot else (2000, -0.1)
    if args.pilot:
        args.sizes = ['small']; args.meshes = ['coarse']
    source_paths = [MATLAB_SOURCE/'solver_main_3pb.m',
                    ABAQUS_SOURCE/'run_3pb_abaqus_OLIVER_T3_FAST.py',
                    ABAQUS_SOURCE/'cdm_umat_2d_OLIVER_T3_FAST.for']
    manifest = dict(utc=datetime.now(timezone.utc).isoformat(), pilot=args.pilot,
                    sizes=SIZES, absolute_mesh_scales=MESHES, configurations=CONFIGS,
                    steps=steps, base_final_displacement_mm=displacement,
                    thickness_mm={'small':50,'large':100}, precision='double',
                    abaqus_equilibrium_controls={'large/medium':80,'large/fine':80,
                        'other_cases':'default', 'attempt_limit_for_extended_cases':12,
                        'field_tolerances':'unchanged Abaqus defaults'},
                    source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
                    scope='Sequential single-process runs. GPU element/damage calculations with CPU sparse assembly/factorization. MATLAB 8-thread library limit; Abaqus 8-thread SMP.')
    path=args.workspace/'manifest.json'
    if path.exists():
        old=json.loads(path.read_text())
        if old['source_sha256']!=manifest['source_sha256'] or old['steps']!=steps:
            raise RuntimeError('Source/settings changed: use a new workspace')
    else:
        path.write_text(json.dumps(manifest,indent=2))
    snapshot=args.workspace/'source_snapshot'
    snapshot.mkdir(exist_ok=True)
    for source in source_paths:
        target=snapshot/source.name
        if not target.exists(): shutil.copy2(source,target)
        if hashlib.sha256(target.read_bytes()).hexdigest()!=manifest['source_sha256'][source.name]:
            raise RuntimeError('Snapshot differs from source manifest')
    # Build exact common meshes first, without competing structural solves.
    for size in args.sizes:
        for mesh in args.meshes:
            common=args.workspace/size/mesh/'common'
            setup(common,snapshot)
            metadata=common/'Gregoire_3PB/matlab_mesh/mesh_metadata.json'
            if args.stage in ['build','all'] and not metadata.exists():
                launch(command_abaqus(common),common,env_abq(size,mesh,steps,displacement,build=True),common/'build.log')
            if not metadata.exists():
                raise RuntimeError('Build the common mesh first')
            existing=json.loads(metadata.read_text())
            if existing['size_scale']!=SIZES[size] or existing['mesh_scale']!=MESHES[mesh] or abs(existing['max_displacement_mm']-displacement*SIZES[size])>1e-12 or abs(existing['max_increment']-1/steps)>1e-12:
                raise RuntimeError('Existing common mesh settings differ')
    if args.stage=='build':
        return
    for size in args.sizes:
        for mesh in args.meshes:
            common=args.workspace/size/mesh/'common/Gregoire_3PB/matlab_mesh'
            expected={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in common.glob('*.txt')}
            for config in args.configs:
                folder=args.workspace/size/mesh/config
                done=folder/'completed.json'
                if done.exists():
                    print('Already complete:',folder,flush=True); continue
                setup(folder,snapshot)
                cpus,backend=CONFIGS[config]
                if backend:
                    result=folder/'results';result.mkdir(exist_ok=True)
                    env=os.environ.copy()
                    env.update(FRACMATH_CASE_DIR=str(common),FRACMATH_RESULTS_DIR=str(result),
                               FRACMATH_HEADLESS='1',FRACMATH_STEPS=str(steps),
                               FRACMATH_MAX_DISP=str(displacement*SIZES[size]),
                               FRACMATH_REGULARIZATION='oliver',FRACMATH_SELFTEST='0',
                               FRACMATH_EQUIVALENT_STRAIN='modified_mises',
                               FRACMATH_SIZE_SCALE=str(SIZES[size]),FRACMATH_THREADS=str(cpus),
                               FRACMATH_BACKEND=backend)
                    solver=str(snapshot).replace("'","''")
                    launch(['matlab','-batch',"addpath('%s');solver_main_3pb"%solver],folder,env,folder/'run.log')
                    if not (result/'verified_state.mat').exists():
                        raise RuntimeError('No complete MATLAB state')
                else:
                    launch(command_abaqus(folder),folder,env_abq(size,mesh,steps,displacement,cpus),folder/'run.log')
                    actual=folder/'Gregoire_3PB/matlab_mesh'
                    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in actual.glob('*.txt')}
                    if hashes!=expected:
                        raise RuntimeError('Abaqus regenerated a different mesh')
                    if not (folder/'Gregoire_3PB/results/abaqus_load_cmod.csv').exists():
                        raise RuntimeError('No complete Abaqus response')
                done.write_text(json.dumps({'config':config,'size':size,'mesh':mesh,'steps':steps,
                                            'mesh_sha256':expected},indent=2))
                print('Completed:',size,mesh,config,flush=True)

if __name__=='__main__':
    main()
