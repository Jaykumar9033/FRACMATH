"""Run two damage-driver examples on one exact mesh and fixed schedule.

python softwarex/run_equivalent_strain_study.py --workspace C:/runs/strain_study --stage all
Numerical runs are sequential. Use a new workspace; saved evidence is not overwritten.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import time

import numpy as np

PACKAGE=Path(__file__).resolve().parent
LABELS={'modified_mises':'Modified von Mises',
        'rankine_stress':'Rankine (stress)'}


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
          'scope':'Damage-driver sensitivity with the same exponential law, tensile onset, energy convention and mesh; not complete concrete models.'}
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
    styles={'modified_mises':('#2166a5','-'),
            'rankine_stress':('#7b3294',':')}
    curves={}
    # The immutable archive also contains optional drivers outside Figure 4.
    for mode in LABELS:
        if mode not in plan['criteria'] or mode not in summary['cases']:
            raise ValueError('Current comparison driver is missing: '+mode)
        values=np.loadtxt(workspace/'runs'/mode/'matlab_load_cmod.csv',delimiter=',',comments='#',ndmin=2)
        if len(values)!=plan['steps'] or not np.isfinite(values).all():
            raise ValueError('Incomplete or non-finite curve: '+mode)
        if abs(float(np.max(values[:,1]))-summary['cases'][mode]['peak_load_N'])>1e-9:
            raise ValueError('Curve peak differs from the verified summary: '+mode)
        curves[mode]=values
    experiment=read_experiment(workspace/'mesh')
    upper_cmod=float(np.ceil(max(values[:,0].max() for values in curves.values())/0.01)*0.01)
    visible=np.flatnonzero(experiment[:,1]<=upper_cmod)
    markers=[];last=-np.inf
    for index in visible:
        if experiment[index,1]-last>=0.006:
            markers.append(int(index));last=experiment[index,1]
    markers=sorted(set(markers+[int(np.argmax(experiment[:,2]))]))
    output.mkdir(parents=True,exist_ok=True)
    with plt.rc_context({'font.size':11,'pdf.fonttype':42}):
        fig,ax=plt.subplots(figsize=(8.4,5.2),layout='constrained')
        for mode,label in LABELS.items():
            values=curves[mode];color,line=styles[mode]
            # Preserve the chronological loading sequence.
            ax.plot(values[:,0],values[:,1]/1000,label=label,color=color,linestyle=line,linewidth=2)
            peak=np.argmax(values[:,1]);ax.plot(values[peak,0],values[peak,1]/1000,'o',color=color,markersize=4)
        ax.plot(experiment[:,1],experiment[:,2],color='#444444',linewidth=1,
                marker='o',markerfacecolor='white',markeredgewidth=1,
                markersize=4.5,markevery=markers,label='Experiment (digitized)',zorder=1)
        ax.set(xlabel='CMOD [mm]',ylabel='Load [kN]',xlim=(0,upper_cmod),ylim=(0,None))
        ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.18)
        ax.legend(frameon=False,fontsize=10,loc='upper right')
        for extension in ('png','pdf'):
            fig.savefig(output/('equivalent_strain_comparison.'+extension),dpi=300)
        plt.close(fig)


def read_experiment(mesh):
    """Read published graphic vertices, with source and nominal-geometry checks."""
    folder=PACKAGE/'reproducibility/experimental_2d'
    provenance=json.loads((folder/'provenance.json').read_text(encoding='utf-8'))
    path=folder/'published_experimental_100mm_vertices.csv'
    if digest(path)!=provenance['data_file_sha256']:
        raise ValueError('Published experimental digitization has changed')
    data=np.loadtxt(path,delimiter=',',skiprows=1,ndmin=2)
    if data.shape!=(provenance['graphic_vertex_count'],5) or not np.isfinite(data).all():
        raise ValueError('Invalid published experimental vertices')
    calibration=provenance['axis_calibration']
    x=(data[:,3]-calibration['x0'])*(calibration['CMOD1_mm']-calibration['CMOD0_mm'])/(calibration['x1']-calibration['x0'])+calibration['CMOD0_mm']
    y=(data[:,4]-calibration['y0'])*(calibration['load1_kN']-calibration['load0_kN'])/(calibration['y1']-calibration['y0'])+calibration['load0_kN']
    if not np.allclose(data[:,1],x,rtol=0,atol=5e-12) or not np.allclose(data[:,2],y,rtol=0,atol=5e-11):
        raise ValueError('Experimental axis calibration failed')
    if np.any(np.diff(data[:,1])<0) or provenance['legend_series']!='experiments 100 mm':
        raise ValueError('Unexpected published experimental trace')
    nodes=np.loadtxt(mesh/'nodes.txt')
    # Compare physical dimensions, not the bibliographic filename.
    coordinates=nodes[:,1:3]
    if not np.allclose(np.ptp(coordinates,axis=0),[350,100],atol=1e-8):
        raise ValueError('Experiment is only supplied for the 350 x 100 mm beam')
    metadata=json.loads((mesh/'mesh_metadata.json').read_text(encoding='utf-8'))
    boundary=metadata['boundary_nodes']
    span=boundary['Support_Right'][0][1]-boundary['Support_Left'][0][1]
    if abs(span-provenance['geometry']['support_span_mm'])>1e-10:
        raise ValueError('Experimental and numerical support spans differ')
    left=boundary['CMOD1'][0][1];right=boundary['CMOD2'][0][1]
    ligament=coordinates[(coordinates[:,0]>left)&(coordinates[:,0]<right),1]
    if not len(ligament) or abs(ligament.min()-provenance['geometry']['notch_depth_mm'])>1e-8:
        raise ValueError('Experimental and numerical notch depths differ')
    source=(mesh.parent/'source_snapshot/solver_main_3pb.m').read_text(encoding='utf-8')
    thickness=re.search(r'p\.t\s*=\s*([\d.]+)',source)
    if not thickness or float(thickness.group(1))!=provenance['geometry']['thickness_mm']:
        raise ValueError('Experimental and numerical thickness differ')
    return data


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
