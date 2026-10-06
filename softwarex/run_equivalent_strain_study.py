"""Run five damage-driver examples on one exact mesh and fixed schedule.

python softwarex/run_equivalent_strain_study.py --workspace C:/runs/strain_study --stage all
Numerical runs are sequential. Use a new workspace; saved evidence is not overwritten.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np

PACKAGE=Path(__file__).resolve().parent
LABELS={'modified_mises':'Modified von Mises', 'elastic_energy':'Elastic energy',
        'mazars':'Mazars', 'rankine_stress':'Rankine (stress)',
        'smooth_rankine_stress':'Smooth Rankine (stress)'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path,data):
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')


def prepare(workspace):
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError('Use an empty new workspace')
    workspace.mkdir(parents=True,exist_ok=True)
    snapshot=workspace/'source_snapshot';snapshot.mkdir()
    solver=PACKAGE/'reproducibility/2d/solver_main_3pb.m'
    for path in [solver,Path(__file__).resolve(),PACKAGE/'analyze_comparison_extension.py',
                 PACKAGE/'run_comparison_extension.py']:
        shutil.copyfile(path,snapshot/path.name)
    mesh=PACKAGE/'reproducibility/fixed_increment_extension/coarse/Gregoire_3PB/matlab_mesh'
    shutil.copytree(mesh,workspace/'mesh')
    plan={'created_utc':datetime.now(timezone.utc).isoformat(),
          'steps':2000,'final_displacement_mm':-0.1,'regularization':'oliver',
          'backend':'cpu','threads':1,'size_scale':1,'criteria':LABELS,
          'mesh_source':str(mesh),
          'mesh_sha256':{p.name:digest(p) for p in (workspace/'mesh').iterdir() if p.is_file()},
          'source_sha256':{p.name:digest(p) for p in snapshot.iterdir()},
          'scope':'Damage-driver sensitivity with the same exponential law, tensile onset, energy convention and mesh; not full Mazars/Rankine concrete models.'}
    save(workspace/'plan.json',plan)
    return plan


def validate(workspace,plan):
    for folder,key in [('mesh','mesh_sha256'),('source_snapshot','source_sha256')]:
        for name,expected in plan[key].items():
            if digest(workspace/folder/name)!=expected:
                raise ValueError('Frozen input changed: '+name)


def run(workspace,plan,stage,matlab):
    status={'pid':os.getpid(),'stage':stage,'status':'running','completed':[]}
    save(workspace/'execution_status.json',status)
    for mode in plan['criteria']:
        folder=workspace/('material_checks' if stage=='checks' else 'runs')/mode
        if folder.exists():
            raise ValueError('Preserve existing attempt; use a fresh workspace: '+str(folder))
        folder.mkdir(parents=True)
        env=os.environ.copy()
        env.update(FRACMATH_CASE_DIR=str(workspace/'mesh'),FRACMATH_RESULTS_DIR=str(folder),
                   FRACMATH_HEADLESS='1',FRACMATH_SELFTEST='1' if stage=='checks' else '0',
                   FRACMATH_STEPS=str(plan['steps']),FRACMATH_MAX_DISP=str(plan['final_displacement_mm']),
                   FRACMATH_REGULARIZATION='oliver',FRACMATH_EQUIVALENT_STRAIN=mode,
                   FRACMATH_THREADS='1',FRACMATH_BACKEND='cpu',FRACMATH_SIZE_SCALE='1',FRACMATH_FIXED_WIDTH='1.25')
        directory=str(workspace/'source_snapshot').replace("'","''")
        started=time.monotonic()
        with (folder/'run.log').open('w',encoding='utf-8') as stream:
            child=subprocess.Popen([matlab,'-batch',"addpath('%s');solver_main_3pb"%directory],
                                   cwd=folder,env=env,stdout=stream,stderr=subprocess.STDOUT)
            status.update(active_criterion=mode,active_child_pid=child.pid)
            save(workspace/'execution_status.json',status)
            code=child.wait()
        record={'return_code':code,'launch_elapsed_s':time.monotonic()-started,
                'criterion':mode,'stage':stage,'status':'executed_needs_verification' if code==0 else 'failed_preserved'}
        save(folder/'execution.json',record)
        if code:
            status.update(status='failed_preserved',failed_criterion=mode)
            save(workspace/'execution_status.json',status)
            raise RuntimeError('MATLAB failed; inspect '+str(folder/'run.log'))
        status['completed'].append(mode)
        save(workspace/'execution_status.json',status)
    status.update(status='executed_needs_verification',active_child_pid=None)
    save(workspace/'execution_status.json',status)


def analyze(workspace,output):
    from analyze_comparison_extension import matlab_check,comparison
    plan=json.loads((workspace/'plan.json').read_text())
    validate(workspace,plan)
    settings={'steps':plan['steps'],'final_displacement_mm':plan['final_displacement_mm']}
    summary={'all_execution_checks_passed':True,'cases':{},'scope':plan['scope']}
    curves={}
    for mode in plan['criteria']:
        material=workspace/'material_checks'/mode
        checks=np.loadtxt(material/('equivalent_strain_check_'+mode+'.csv'),delimiter=',',ndmin=2)
        energy=np.loadtxt(material/'material_energy.csv',delimiter=',',ndmin=2)
        if len(checks)!=10 or not np.isfinite(checks).all() or not np.allclose(checks[:,4],checks[:,5],atol=2e-12,rtol=0):
            raise ValueError('Independent equivalent-strain check failed: '+mode)
        if not np.isfinite(energy).all() or np.max(np.abs(energy[:,2]))>=.01:
            raise ValueError('Uniaxial fracture-energy check failed: '+mode)
        checked,curves[mode]=matlab_check(workspace/'runs'/mode,workspace/'mesh',settings,'oliver',mode)
        checked.update(independent_material_states=10,
                       maximum_equivalent_strain_error=float(np.max(np.abs(checks[:,4]-checks[:,5]))),
                       maximum_uniaxial_energy_relative_error=float(np.max(np.abs(energy[:,2]))))
        summary['cases'][mode]=checked
    for mode in plan['criteria']:
        summary['cases'][mode]['relative_to_modified_mises']=comparison(curves['modified_mises'],curves[mode])
    output.mkdir(parents=True,exist_ok=True)
    save(output/'summary.json',summary)
    plot(workspace,output,summary)
    return summary


def plot(workspace,output,summary=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plan=json.loads((workspace/'plan.json').read_text())
    validate(workspace,plan)
    if summary is None:
        summary=json.loads((workspace/'analysis/summary.json').read_text())
    if not summary['all_execution_checks_passed']:
        raise ValueError('Only fully checked cases can be plotted')
    styles=[('#2166a5','-'),('#cc503e','--'),('#238b45','-.'),('#7b3294',':'),('#b57900',(0,(5,1,1,1)))]
    curves={}
    for mode in plan['criteria']:
        values=np.loadtxt(workspace/'runs'/mode/'matlab_load_cmod.csv',delimiter=',',comments='#',ndmin=2)
        history=np.genfromtxt(workspace/'runs'/mode/'matlab_energy_history.csv',delimiter=',',names=True)
        if len(values)!=plan['steps'] or not np.isfinite(values).all():
            raise ValueError('Incomplete or non-finite curve: '+mode)
        if len(history)!=len(values) or not np.isfinite(history['displacement_mm']).all():
            raise ValueError('Invalid prescribed-displacement history: '+mode)
        if abs(float(np.max(values[:,1]))-summary['cases'][mode]['peak_load_N'])>1e-9:
            raise ValueError('Curve peak differs from the verified summary: '+mode)
        curves[mode]=(values,history['displacement_mm'])
    output.mkdir(parents=True,exist_ok=True)
    with plt.rc_context({'font.size':11,'pdf.fonttype':42}):
        fig,axes=plt.subplots(2,1,figsize=(8.4,8.6),layout='constrained')
        for panel,ax in enumerate(axes):
            for (mode,label),(color,line) in zip(plan['criteria'].items(),styles):
                values,displacement=curves[mode]
                x=displacement if panel==0 else values[:,0]
                ax.plot(x,values[:,1]/1000,label=label,color=color,linestyle=line,linewidth=2)
                peak=np.argmax(values[:,1]);ax.plot(x[peak],values[peak,1]/1000,'o',color=color,markersize=4)
            ax.set(xlabel='Prescribed downward displacement [mm]' if panel==0 else 'CMOD [mm]',
                   ylabel='Load [kN]',xlim=(0,None),ylim=(0,None))
            ax.set_title('(a) Response to prescribed loading' if panel==0 else '(b) Crack-mouth opening response',loc='left',fontsize=11)
            ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.18)
        axes[0].legend(frameon=False,fontsize=9.5,loc='upper right')
        for extension in ('png','pdf'):
            fig.savefig(output/('equivalent_strain_comparison.'+extension),dpi=300)
        plt.close(fig)
        fig,ax=plt.subplots(figsize=(8.4,5.2),layout='constrained')
        for (mode,label),(color,line) in zip(plan['criteria'].items(),styles):
            values,displacement=curves[mode]
            ax.plot(displacement,values[:,1]/1000,label=label,color=color,linestyle=line,linewidth=2)
            peak=np.argmax(values[:,1]);ax.plot(displacement[peak],values[peak,1]/1000,'o',color=color,markersize=4)
        ax.set(xlabel='Prescribed downward displacement [mm]',ylabel='Load [kN]',xlim=(0,None),ylim=(0,None))
        ax.set_title('Same coarse mesh, Oliver width and 2,000 fixed increments')
        ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.18)
        ax.legend(frameon=False,fontsize=10)
        for extension in ('png','pdf'):
            fig.savefig(output/('equivalent_strain_load_displacement.'+extension),dpi=300)
        plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--stage',choices=['prepare','checks','solve','analyze','all'],default='prepare')
    parser.add_argument('--matlab',default='matlab')
    parser.add_argument('--output',type=Path,help='Separate output folder required for the analysis-only stage')
    args=parser.parse_args();workspace=args.workspace.resolve()
    if args.stage=='analyze' and args.output is None:
        parser.error('Provide --output to preserve the archived result files')
    if args.stage=='analyze':
        output=args.output.resolve()
        if output.is_relative_to(workspace) or (output.exists() and any(output.iterdir())):
            parser.error('Use an empty output folder outside the archived workspace')
    plan=prepare(workspace) if args.stage in ('prepare','all') else json.loads((workspace/'plan.json').read_text())
    validate(workspace,plan)
    if args.stage in ('checks','all'):run(workspace,plan,'checks',args.matlab)
    if args.stage in ('solve','all'):run(workspace,plan,'solve',args.matlab)
    if args.stage in ('analyze','all'):
        analyze(workspace,args.output.resolve() if args.output else workspace/'analysis')
        if args.stage=='all':
            save(workspace/'execution_status.json',{'status':'verified_complete','pid':os.getpid(),'criteria':list(plan['criteria'])})


if __name__=='__main__':
    main()
