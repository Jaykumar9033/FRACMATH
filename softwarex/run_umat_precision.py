"""Repeatable Windows material-point timing and history verification.

No production UMAT changes. Batch timings include driver work. They are
standalone measurements, not Abaqus job phases or element assembly costs.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
import numpy as np
from audit_umat import prepare, reference, check

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'reproducibility/abaqus/cdm_umat_2d_OLIVER_T3_FAST.for'


def history_cases(folder):
    prepare(folder)
    rows=np.loadtxt(folder/'point_inputs.csv',delimiter=',').tolist()
    metadata=[]
    for element in range(1,5):
        for path in ['tension','shear','compression','rotation']:
            state=np.zeros(2)
            for step,amplitude in enumerate([0.,.0002,.0008,.0001,0.,.0004,.0012]):
                if path=='tension': strain=np.array([amplitude,-.2*amplitude,0.])
                elif path=='shear': strain=np.array([0.,0.,amplitude])
                elif path=='compression': strain=np.array([-amplitude,.2*amplitude,0.])
                else:
                    angle=.15*step;c=np.cos(angle);s=np.sin(angle)
                    strain=amplitude*np.array([c*c-.2*s*s,s*s-.2*c*c,2*1.2*c*s])
                row=np.r_[len(rows)+1,element,.3*strain,.7*strain,state]
                state=reference(row)[3:5];rows.append(row.tolist())
                metadata.append(dict(case=len(rows),element=element,path=path,step=step))
    np.savetxt(folder/'point_inputs.csv',rows,delimiter=',',fmt='%.17g')
    (folder/'history_paths.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')


def command_file(folder,driver,executable,extra=''):
    content='@echo off\n'+(
        'call "C:\\Program Files (x86)\\Intel\\oneAPI\\compiler\\2025.0\\env\\vars.bat" intel64 vs2022\n'
        'if errorlevel 1 exit /b 1\n'
        'ifx /O2 /extend-source /names:lowercase '
        '/include:"C:\\SIMULIA\\EstProducts\\2024\\SMAUsubs\\PublicInterfaces" '
        'cdm_umat_2d_OLIVER_T3_FAST.for '+extra+' '+driver+' /exe:'+executable+'\n'
        'if errorlevel 1 exit /b 1\n'+executable+'\n')
    # Normalize path separators in these Windows command arguments.
    content=content.replace('\\\\','\\')
    (folder/'compile_run.cmd').write_text(content,encoding='utf-8')


def prepare_all(folder):
    if folder.exists(): raise ValueError('Use a new workspace')
    batch=folder/'batch';history=folder/'history';batch.mkdir(parents=True)
    for name in ['point_inputs.csv','oliver_t3_gradN.dat']:
        shutil.copy2(HERE/'reproducibility/umat_audit'/name,batch/name)
    shutil.copy2(SOURCE,batch/SOURCE.name)
    shutil.copy2(HERE/'benchmark_umat_batches.f90',batch/'benchmark_umat_batches.f90')
    source=SOURCE.read_text()
    empty=source[:source.index('C----- Material constants')].replace(
        'SUBROUTINE UMAT(','SUBROUTINE EMPTY_UMAT(',1)+'      RETURN\n      END\n'
    (batch/'empty_umat.for').write_text(empty)
    command_file(batch,'benchmark_umat_batches.f90','benchmark_umat_batches.exe','empty_umat.for kernel32.lib')
    history_cases(history)
    for name in ['umat_point_audit.f90']:shutil.copy2(HERE/name,history/name)
    shutil.copy2(SOURCE,history/SOURCE.name)
    command_file(history,'umat_point_audit.f90','umat_point_audit.exe')


def analyze(folder):
    batch=folder/'batch';history=folder/'history'
    for location in [batch,history]:
        if (location/SOURCE.name).read_bytes()!=SOURCE.read_bytes():
            raise ValueError('Production source bytes differ')
    check(history)
    values=np.genfromtxt(batch/'batch_timings.csv',delimiter=',',names=True)
    calibration=np.genfromtxt(batch/'clock_calibration.csv',delimiter=',',names=True)
    if len(values)!=10:raise ValueError('Expected five actual and five control observations')
    actual=values[values['mode']==1];control=values[values['mode']==2]
    if not np.all(values['calls']==14240000) or not np.all(values['elapsed_s']>0):
        raise ValueError('Invalid batch observations')
    for observations in [actual,control]:
        if set(observations['repeat'])!=set(range(1,6)):
            raise ValueError('Missing or repeated batch')
    inputs=np.loadtxt(batch/'point_inputs.csv',delimiter=',')
    expected=20000*sum(np.sum(reference(row)[:3])+np.sum(reference(row)[3:7])+
                       np.sum(reference(row)[7:]) for row in inputs)
    if not np.allclose(actual['checksum'],expected,rtol=1e-9,atol=1e-6):
        raise ValueError('UMAT batch checksum differs from independent reference')
    expected_control=20000*np.sum(inputs[:,8:10])
    if not np.allclose(control['checksum'],expected_control,rtol=1e-9,atol=1e-6):
        raise ValueError('Empty-driver checksum differs')
    def statistics(observations):
        times=observations['elapsed_s']
        return dict(median_elapsed_s=float(np.median(times)),min_elapsed_s=float(times.min()),
                    max_elapsed_s=float(times.max()),
                    coefficient_of_variation_percent=float(100*np.std(times,ddof=1)/np.mean(times)))
    report=dict(scope='Standalone unchanged UMAT; 712 material inputs with four state variables; driver work included.',
                actual=statistics(actual),empty_driver=statistics(control),repeats=5,
                calls_per_repeat=14240000,total_actual_calls=71200000,
                clock_frequency_hz=int(calibration['rate_hz']),
                calibrated_pair_mean_s=float(calibration['mean_pair_s']),
                observed_min_positive_clock_delta_s=float(calibration['min_positive_delta_s']),
                clock_pairs_per_batch=1,
                independent_checksums_pass=True,production_umat_bytes_identical=True,
                production_umat_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                material_verification=json.loads((history/'summary.json').read_text()),
                limitations=['Driver resets, call overhead and checksums are included.',
                    'Empty-driver time is reported separately; no exact overhead subtraction.',
                    'Synthetic cached material inputs are not a structural Abaqus workload.',
                    'Compiler flags and NSTATV=4 differ in scope from Abaqus job execution.',
                    'No assembly, full job, or individual-block performance percentages inferred.'])
    if (folder/'fresh_replay').exists():
        analyze(folder/'fresh_replay')
        second=json.loads((folder/'fresh_replay/summary.json').read_text())
        replay=np.genfromtxt(folder/'fresh_replay/batch/batch_timings.csv',delimiter=',',names=True)
        observations=np.concatenate([values,replay])
        report['fresh_replay']={key:second[key] for key in
            ['actual','empty_driver','production_umat_bytes_identical','independent_checksums_pass']}
        report['combined_actual']=statistics(observations[observations['mode']==1])
        report['combined_empty_driver']=statistics(observations[observations['mode']==2])
        report['total_actual_calls_both_processes']=142400000
        report['combined_batches']=10
    (folder/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--analyze-only',action='store_true')
    parser.add_argument('--matlab',default=r'C:\Program Files\MATLAB\R2024b\bin\matlab.exe')
    args=parser.parse_args();folder=args.workspace.resolve()
    if args.prepare_only and args.analyze_only:parser.error('Choose one mode')
    if not args.analyze_only:
        prepare_all(folder)
        if args.prepare_only:return
        for name in ['batch','history']:
            with (folder/name/'compile_and_run.log').open('w') as stream:
                subprocess.run(['cmd.exe','/d','/c','compile_run.cmd'],cwd=folder/name,
                               stdout=stream,stderr=subprocess.STDOUT,check=True)
        with (folder/'history/matlab_run.log').open('w') as stream:
            subprocess.run([args.matlab,'-batch','run_matlab_points'],cwd=folder/'history',
                           stdout=stream,stderr=subprocess.STDOUT,check=True)
    analyze(folder)

if __name__=='__main__':main()
