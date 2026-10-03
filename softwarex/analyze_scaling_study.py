"""Validate completed scaling runs and report measured costs and response differences."""
import argparse
import csv
import json
from pathlib import Path
import re
import numpy as np
from scipy.io import loadmat
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze_mesh_study import number
from compare_solver_diagnostics import summarize
from run_scaling_study import SIZES, MESHES, CONFIGS

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((args.workspace/'manifest.json').read_text())
    sizes=['small'] if manifest['pilot'] else list(SIZES)
    meshes=['coarse'] if manifest['pilot'] else list(MESHES)
    rows=[]; curves={}; missing=[]
    for size in sizes:
        for mesh in meshes:
            base=args.workspace/size/mesh
            meta=json.loads((base/'common/Gregoire_3PB/matlab_mesh/mesh_metadata.json').read_text())
            for config in CONFIGS:
                folder=base/config
                if not (folder/'completed.json').exists():
                    missing.append('/'.join([size,mesh,config])); continue
                row=dict(size=size,mesh=mesh,config=config,elements=meta['elements'],dofs=meta['dofs'],depth_mm=meta['depth_mm'],thickness_mm=meta['thickness_mm'],requested_threads=CONFIGS[config][0])
                sampling=json.loads((folder/'run.sampling.json').read_text())
                row['launch_to_exit_s']=sampling['launch_elapsed_s']
                if config.startswith('matlab'):
                    result=folder/'results'
                    curve=np.loadtxt(result/'matlab_load_cmod.csv',delimiter=',',comments='#')
                    diag=np.genfromtxt(result/'matlab_step_diagnostics.csv',delimiter=',',names=True)
                    if len(curve)!=manifest['steps'] or not np.all(diag['old_damage_converged']==1):
                        raise ValueError('Incomplete or unconverged old-damage history')
                    timing=(result/'matlab_timing.txt').read_text()
                    if number(r'Computational threads:\s*(\d+)',timing)!=CONFIGS[config][0] or ('Backend: '+CONFIGS[config][1]) not in timing:
                        raise ValueError('MATLAB computing configuration mismatch')
                    if CONFIGS[config][1]=='gpu_hybrid' and 'double precision; CPU sparse assembly/factorization' not in timing:
                        raise ValueError('Missing GPU precision/scope record')
                    row['wall_s']=number(r'Solver wall-clock:\s*([\d.]+)',timing)
                    for key in ['assembly','factorization','damage','solve']:
                        row[key+'_s']=number(key+r':\s*([\d.]+)',timing)
                    row['peak_working_set_MB']=number(r'Peak process working set:\s*([\d.]+)',timing,False)
                    row['max_post_damage_residual']=float(diag['post_damage_relative_residual'].max())
                else:
                    job=folder/'Gregoire_3PB'
                    sta=(job/'Gregoire_3PB.sta').read_text(errors='replace')
                    sta_rows=[line.split() for line in sta.splitlines() if re.match(r'^\s+1\s+\d+\s+',line)]
                    if 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' not in sta or not sta_rows or abs(float(sta_rows[-1][7])-1)>1e-8:
                        raise ValueError('Incomplete Abaqus load history')
                    actual_meta=json.loads((job/'matlab_mesh/mesh_metadata.json').read_text())
                    for key in ['size_scale','mesh_scale','thickness_mm','max_displacement_mm','max_increment']:
                        if actual_meta[key]!=meta[key]:raise ValueError('Abaqus geometry/loading metadata mismatch')
                    inp=(job/'Gregoire_3PB.inp').read_text(errors='replace')
                    if re.search(r'^\*Output.*variable=PRESELECT',inp,re.I|re.M):
                        raise ValueError('Unexpected default Abaqus output request')
                    freq=re.search(r'^\*Output, field, frequency=(\d+)',inp,re.I|re.M)
                    row['field_output_increment_frequency']=max(1,manifest['steps']//20)
                    if not freq or int(freq.group(1))!=row['field_output_increment_frequency']:
                        raise ValueError('Unexpected Abaqus field output frequency')
                    extended=size=='large' and mesh in ['medium','fine']
                    row['equilibrium_iteration_limit']=80 if extended else 16
                    row['increment_attempt_limit']=12 if extended else 5
                    control=re.search(r'^\*Controls, parameters=TIME INCREMENTATION[^\n]*\n([^\n]+)',inp,re.I|re.M)
                    if extended:
                        if not control:raise ValueError('Missing declared extended iteration controls')
                        items=control.group(1).split(',')
                        defaults=[4,8,9,16,10,4,12,5,6,3,50]
                        values=[float(v) if v.strip() else defaults[i] for i,v in enumerate(items)]
                        if values != [4,8,9,80,10,4,12,12,6,3,80]:
                            raise ValueError('Unexpected iteration controls')
                    elif control:
                        raise ValueError('Unexpected controls in default-control case')
                    row['odb_bytes']=(job/'Gregoire_3PB.odb').stat().st_size if (job/'Gregoire_3PB.odb').exists() else None
                    parsed=summarize(base/'matlab_cpu1/results/matlab_timing.txt',job/'Gregoire_3PB.msg')['abaqus']
                    msg=(job/'Gregoire_3PB.msg').read_text(errors='replace')
                    actual_threads=re.findall(r'1 MPI RANK PER HOST x\s+(\d+) THREADS? PER RANK',msg)
                    if not actual_threads or any(int(v)!=CONFIGS[config][0] for v in actual_threads):
                        raise ValueError('Abaqus SMP computing configuration mismatch')
                    row['observed_solver_threads']=int(actual_threads[0])
                    row.update(parsed)
                    curve=np.loadtxt(job/'results/abaqus_load_cmod.csv',delimiter=',',comments='#')
                    log=(job/'Gregoire_3PB.log').read_text(errors='replace')
                    loaded=re.search(r'UMAT FAST:\s*Oliver T3 gradN table loaded, n=\s*(\d+)',log)
                    if not loaded or int(loaded.group(1))!=meta['elements'] or 'CELENT fallback' in log:
                        raise ValueError('Invalid Oliver table initialization')
                    row['peak_working_set_MB']=sampling['standard_sampled_peak_working_set_MB']
                    dat=(job/'Gregoire_3PB.dat').read_text(errors='replace')
                    for label,key in [('USER TIME','analysis_user_cpu_s'),('SYSTEM TIME','analysis_system_cpu_s'),('TOTAL CPU TIME','analysis_total_cpu_s')]:
                        matches=re.findall(re.escape(label)+r'\s*\(SEC\)\s*=\s*([0-9.E+\-]+)',dat)
                        if not matches: raise ValueError('Missing CPU timer')
                        row[key]=float(matches[-1])
                if not np.isfinite(curve).all() or curve[:,1].max()<=0:
                    raise ValueError('Invalid load history')
                peak=int(np.argmax(curve[:,1])); row['peak_N']=float(curve[peak,1]);row['peak_cmod_mm']=float(curve[peak,0])
                if config.startswith('matlab'):
                    state=loadmat(result/'verified_state.mat',variable_names=['F','p','omega','CMOD'],simplify_cells=True)
                    curve[:,1]=np.asarray(state['F']).ravel()
                    curve[:,0]=np.asarray(state['CMOD']).ravel()
                    peak=int(np.argmax(curve[:,1])); row['peak_N']=float(curve[peak,1]); row['peak_cmod_mm']=float(curve[peak,0])
                    if abs(state['p']['t']-50*SIZES[size])>1e-12 or abs(state['p']['max_disp']-manifest['base_final_displacement_mm']*SIZES[size])>1e-12:
                        raise ValueError('MATLAB geometry/loading mismatch')
                row['peak_nominal_bending_stress_MPa']=3.75*row['peak_N']/(row['thickness_mm']*row['depth_mm'])
                curves[(size,mesh,config)]=curve;rows.append(row)
    for row in rows:
        size,mesh,config=[row[k] for k in ['size','mesh','config']]
        reference='abaqus_cpu1' if config.startswith('abaqus') else 'matlab_cpu1'
        ref=next((r for r in rows if (r['size'],r['mesh'],r['config'])==(size,mesh,reference)),None)
        if ref:
            row['within_program_speed_ratio']=ref['wall_s']/row['wall_s']
            row['peak_change_from_program_cpu1_percent']=100*(row['peak_N']/ref['peak_N']-1)
            a=curves[(size,mesh,config)];b=curves[(size,mesh,reference)]
            # Explicitly compare ordered load history too; adaptive Abaqus records use time/CMOD separately.
            if config.startswith('matlab'):
                row['max_load_history_difference_fraction']=float(np.max(np.abs(a[:,1]-b[:,1]))/b[:,1].max())
                current=loadmat(args.workspace/size/mesh/config/'results/verified_state.mat',variable_names=['omega'],simplify_cells=True)['omega']
                reference_damage=loadmat(args.workspace/size/mesh/reference/'results/verified_state.mat',variable_names=['omega'],simplify_cells=True)['omega']
                row['max_final_damage_difference']=float(np.max(np.abs(current-reference_damage)))
                row['hardware_response_check']=row['max_load_history_difference_fraction']<=1e-3 and row['max_final_damage_difference']<=1e-4
            else:
                if np.any(np.diff(a[:,0]) < -1e-8) or np.any(np.diff(b[:,0]) < -1e-8):
                    row['hardware_response_check']=False
                    row['curve_check_note']='Non-monotone CMOD requires explicit branch comparison'
                else:
                    grid=np.linspace(max(a[0,0],b[0,0]),min(a[-1,0],b[-1,0]),1001)
                    difference=np.interp(grid,a[:,0],a[:,1])-np.interp(grid,b[:,0],b[:,1])
                    row['max_load_curve_difference_fraction']=float(np.max(np.abs(difference))/b[:,1].max())
                    row['hardware_response_check']=abs(row['peak_change_from_program_cpu1_percent'])<=0.1 and row['max_load_curve_difference_fraction']<=1e-3
            if not row['hardware_response_check']:
                row['within_program_speed_ratio']=None
    for row in rows:
        reference=next((r for r in rows if r['size']==row['size'] and r['mesh']==row['mesh'] and r['config']=='abaqus_cpu1'),None)
        if reference and row['config'].startswith('matlab'):
            row['peak_difference_from_abaqus_cpu1_percent']=100*(row['peak_N']/reference['peak_N']-1)
    summary={'manifest':manifest,'completed':len(rows),'expected':len(sizes)*len(meshes)*len(CONFIGS),'missing':missing,'runs':rows,
             'interpretation':'One observation per configuration. MATLAB damage update is sequential; Abaqus uses converged increment equilibrium. Cross-program timings are descriptive, not an accuracy-matched speed ranking. Within-program hardware ratios require passing response checks. GPU means hybrid element/damage work, not GPU sparse factorization.'}
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2))
    if rows:
        fields=list(dict.fromkeys(k for r in rows for k in r))
        with (args.output/'timings.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
        plt.rcParams.update({'font.size':12,'axes.titlesize':13,'axes.labelsize':12,'xtick.labelsize':11,'ytick.labelsize':11})
        fig,axes=plt.subplots(len(sizes),len(meshes),figsize=(3*len(meshes),3.1*len(sizes)),squeeze=False,layout='constrained')
        for i,size in enumerate(sizes):
            for j,mesh in enumerate(meshes):
                a=axes[i,j]; rs=[r for r in rows if r['size']==size and r['mesh']==mesh]
                colors={'matlab_cpu1':'#2864A5','matlab_cpu8':'#279287','matlab_gpu_hybrid':'#E58B28','abaqus_cpu1':'#747A83','abaqus_cpu8':'#8A64AE'}
                a.bar(range(len(rs)),[r['wall_s'] for r in rs],color=[colors[r['config']] for r in rs]);a.set_xticks(range(len(rs)),[{'matlab_cpu1':'MAT CPU1','matlab_cpu8':'MAT CPU8','matlab_gpu_hybrid':'MAT GPU','abaqus_cpu1':'ABA CPU1','abaqus_cpu8':'ABA CPU8'}[r['config']] for r in rs],rotation=45,ha='right',fontsize=11)
                a.set(title=size+' / '+mesh,ylabel='Measured time (s)');a.grid(axis='y',alpha=.2)
        fig.savefig(args.output/'scaling_timings.png',dpi=220);fig.savefig(args.output/'scaling_timings.pdf')
        plt.close(fig)
        fig,axes=plt.subplots(len(sizes),len(meshes),figsize=(3*len(meshes),3.1*len(sizes)),squeeze=False,layout='constrained')
        for i,size in enumerate(sizes):
            for j,mesh in enumerate(meshes):
                a=axes[i,j]
                for config,label in [('matlab_cpu1','MATLAB CPU1'),('abaqus_cpu1','Abaqus CPU1')]:
                    key=(size,mesh,config)
                    if key in curves:
                        c=curves[key];depth=100*SIZES[size];thickness=50*SIZES[size]
                        a.plot(c[:,0]/depth,3.75*c[:,1]/(thickness*depth),label=label)
                a.set(title=size+' / '+mesh,xlabel='CMOD / depth',ylabel='Nominal bending stress (MPa)')
                a.ticklabel_format(axis='x',style='sci',scilimits=(0,0));a.grid(alpha=.2)
                if i==0 and j==0:a.legend(fontsize=9)
        fig.savefig(args.output/'scaling_responses.png',dpi=220);fig.savefig(args.output/'scaling_responses.pdf');plt.close(fig)
        if not missing and not manifest['pilot']:
            table=[r'\begin{table}[htbp]',r'\centering\small',
                   r'\caption{Size/mesh computing study: measured time in seconds, one run per setting. MATLAB times cover the load loop; Abaqus times cover analysis and output. All runs use 2{,}000 fixed (MATLAB) or maximum (Abaqus) increments. GPU denotes the hybrid backend with CPU sparse factorization.}',
                   r'\label{tab:scaling}',r'\begin{tabular}{llrrrrrr}',r'\hline',
                   r'Size & Mesh & DOFs & MAT 1 & MAT 8 & MAT GPU & ABA 1 & ABA 8 \\',r'\hline']
            for size in sizes:
                for mesh in meshes:
                    rs=[next(r for r in rows if (r['size'],r['mesh'],r['config'])==(size,mesh,c)) for c in CONFIGS]
                    values=[('%.1f' if r['config'].startswith('matlab') else '%.0f')%r['wall_s'] for r in rs]
                    table.append(' & '.join([size.capitalize(),mesh,format(rs[0]['dofs'],','),*values])+r' \\')
            table.extend([r'\hline',r'\end{tabular}',r'\end{table}'])
            (args.output/'scaling_table.tex').write_text('\n'.join(table)+'\n',encoding='utf-8')
    print('Completed %d/%d; missing %d'%(len(rows),summary['expected'],len(missing)))
    for row in rows: print(row)

if __name__=='__main__': main()
