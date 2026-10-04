"""Report completed, geometry-matched 3D cases and exclude failed histories."""
import argparse
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',required=True,type=Path)
    parser.add_argument('--require-all',action='store_true',
                        help='Fail the final verification gate unless all three meshes finish')
    args=parser.parse_args()
    package=Path(__file__).resolve().parent
    experiment=np.loadtxt(package/'reproducibility/experimental_3d/nooru_47_05_digitized.csv',delimiter=',',skiprows=1)
    fig,ax=plt.subplots(figsize=(6,3.5),layout='constrained')
    ax.plot(experiment[:,0],experiment[:,1]/1000,'ko-',ms=3,lw=1,label='47-05 experiment (digitized)')
    accepted=[]
    excluded=[]
    curves={}
    for name in ['coarse','medium','fine']:
        folder=args.workspace/name
        record=json.loads((folder/'completion.json').read_text())
        if not record['completed']:
            excluded.append(record)
            continue
        meta=json.loads((folder/'mesh_metadata.json').read_text())
        if meta['notch_depth_mm']!=25 or meta['notch_width_mm']!=5:
            raise ValueError('Experimental geometry mismatch')
        history=np.loadtxt(folder/'Job-1_gauge_results.csv',delimiter=',')
        targets=np.loadtxt(folder/'accepted_targets.csv',delimiter=',')
        if len(history)!=len(targets) or not np.isfinite(history).all() or history[:,6].max()>1e-6:
            raise ValueError('Incomplete or unconverged accepted 3D history')
        x=history[:,2:6].mean(axis=1)
        gauge_error=float(np.max(np.abs(x-0.2*targets[:,0])))
        if gauge_error>1e-8 or abs(x[-1]-0.2)>1e-8 or np.any(np.diff(x)<=0):
            raise ValueError('Invalid gauge path')
        x=np.r_[0,x]
        y=np.r_[0,history[:,1]]
        grid=np.linspace(0,min(x[-1],experiment[-1,0]),1001)
        difference=np.interp(grid,x,y)-np.interp(grid,experiment[:,0],experiment[:,1])
        peak=int(np.argmax(y))
        result=dict(mesh=name,nodes=meta['nodes'],elements=meta['elements'],dofs=meta['dofs'],
                    accepted_increments=len(history),rejected_trials=int(np.loadtxt(folder/'rejected_trial_count.csv')),
                    peak_N=float(y[peak]),peak_gauge_mm=float(x[peak]),
                    peak_error_percent=float(100*(y[peak]/experiment[:,1].max()-1)),
                    curve_NRMSE_percent=float(100*np.sqrt(np.mean(difference**2))/experiment[:,1].max()),
                    max_equilibrium_residual=float(history[:,6].max()),max_gauge_constraint_error_mm=gauge_error)
        accepted.append(result)
        curves[name]=(x,y)
        ax.plot(x,y/1000,lw=1.3,label='%s: %s TET4' % (name,format(meta['elements'],',')))
    if accepted:
        peaks=[row['peak_N'] for row in accepted]
        spread=100*(max(peaks)-min(peaks))/np.mean(peaks)
    else:
        spread=None
    response_difference=None
    if 'medium' in curves and 'fine' in curves:
        grid=np.linspace(0,0.2,1001)
        medium=np.interp(grid,*curves['medium'])
        fine=np.interp(grid,*curves['fine'])
        response_difference=100*float(np.sqrt(np.mean((medium-fine)**2)))/max(curves['fine'][1])
    summary=dict(experimental_peak_N=float(experiment[:,1].max()),accepted=accepted,excluded=excluded,
                 completed_meshes=len(accepted),peak_mesh_spread_percent=spread,
                 medium_fine_curve_RMS_difference_percent_of_fine_peak=response_difference,
                 scope='One pure-tension geometry with published 25 mm notches; three prescribed mesh seeds, local gauges and unchanged material parameters. Target bisections retain equilibrium tolerances. Does not establish general 3D mesh or orientation independence.')
    output=args.workspace/'analysis'
    output.mkdir(exist_ok=True)
    (output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    if accepted:
        ax.set(xlabel='Mean 65 mm gauge displacement (mm)',ylabel='Normal load (kN)',xlim=(0,0.2))
        ax.grid(alpha=0.2)
        ax.legend(fontsize=7)
        for suffix in ['png','pdf']:
            fig.savefig(output/('nooru_tension_mesh_comparison.'+suffix),dpi=300)
    print(json.dumps(summary,indent=2))
    if args.require_all and len(accepted)!=3:
        raise SystemExit('The complete three-mesh verification gate is not satisfied')


if __name__=='__main__':
    main()
