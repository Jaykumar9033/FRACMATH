"""Run three published-geometry 3D pure-tension meshes with strict equilibrium.

The nominal notch depth is 25 mm and width is 5 mm. Optional target bisection
rejects failed trials before committing damage; all accepted trials retain
the 1e-6 equilibrium tolerance. Results are separate from illustrative images.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import numpy as np


def create_solver(source, target):
    text = source.read_text(encoding='utf-8')
    old = "for s = 1:nIncr\n    lambda_load = s/nIncr;"
    new = """targets = (1:nIncr)'/nIncr;
s = 1;
rejected_trials = 0;
while s <= numel(targets)
    lambda_load = targets(s);"""
    if old not in text:
        raise ValueError('Unexpected 3D source loop')
    text = text.replace(old,new,1)
    old = """    if ~converged
        if strict_equilibrium, error('Equilibrium did not converge at increment %d: residual %.3e',s,relres); end
        warning('Newton did not fully converge at increment %d. it=%d, relres=%.3e', s, it, relres);
    end"""
    new = """    if ~converged
        previous_target = 0;
        if s>1, previous_target=targets(s-1); end
        gap=targets(s)-previous_target;
        if gap < 1e-7 || rejected_trials >= 500
            error('Target bisection exhausted at accepted increment %d, target %.9g, residual %.3e',s-1,targets(s),relres);
        end
        fprintf('Rejected trial at target %.9g, residual %.3e; bisecting target.\\n',targets(s),relres);
        targets=[targets(1:s-1);previous_target+gap/2;targets(s:end)];
        rejected_trials=rejected_trials+1;
        continue;
    end"""
    if old not in text:
        raise ValueError('Unexpected 3D convergence branch')
    text = text.replace(old,new,1)
    old = "end\n\nelapsed = toc(tic_total);"
    new = """    s = s+1;
end
nIncr = numel(targets);
writematrix([targets,relres_res,iter_res],'accepted_targets.csv');
writematrix(rejected_trials,'rejected_trial_count.csv');
elapsed = toc(tic_total);"""
    if old not in text:
        raise ValueError('Unexpected 3D source loop end')
    text = text.replace(old,new,1)
    # Numerical histories grow on every accepted adaptive increment. Extend
    # the optional image-name column too, even when snapshots are disabled.
    old = '    do_save = '
    if old not in text:
        raise ValueError('Unexpected 3D snapshot branch')
    text = text.replace(old, "    saved_png{s,1} = '';\n" + old, 1)
    # Retain both history variables: a changing directional width must not
    # reduce damage, even when the equivalent-strain maximum stays fixed.
    text = re.sub(r'\bkappa\b', 'history', text)
    text = re.sub(r'\bkappa_old\b', 'history_old', text)
    old = 'history = j0 * ones(ne,1);'
    if old not in text:
        raise ValueError('Unexpected 3D history initialization')
    text = text.replace(old,"history = struct('kappa', j0*ones(ne,1), 'omega', zeros(ne,1));",1)
    old = 'history = max(history, eeq_bc);'
    if old not in text:
        raise ValueError('Unexpected 3D history commit')
    text = text.replace(old,'history.kappa = max(history.kappa, eeq_bc);\n    history.omega = max(history.omega, De_bc);',1)
    text = text.replace('kappa_trial = max(history_old, eeq);',
                        'kappa_trial = max(history_old.kappa, eeq);',1)
    text = text.replace('De = min(max(De,0),0.999999);',
                        'De = max(min(max(De,0),0.999999), history_old.omega);',1)
    start = text.index('function s = material_scale(')
    end = text.index('function [B_all,V_el,gradN_all,valid]',start)
    material = """function s = material_scale(epsv,E,nu,k,j0,GF,gradN,method,history_old)
[eeq,n] = eqv_strain_modified_vm_vec(epsv,nu,k);
h = oliver_bandwidth_TET4(gradN,n,method);
kappa_trial = max(history_old.kappa,reshape(eeq,[],1));
damage = zeros(size(kappa_trial));
active = kappa_trial>=j0;
b = E*j0/GF*h(:);
damage(active) = 1-j0./kappa_trial(active).*exp(-b(active).*(kappa_trial(active)-j0));
damage = max(min(max(damage,0),0.999999),history_old.omega);
s = E*max(1-damage,1e-8);
end

"""
    text = text[:start]+material+text[end:]
    target.write_text(text,encoding='utf-8')


def gauges(folder, metadata):
    nodes = np.loadtxt(folder/'Job-1_nodes.txt')
    elements = np.loadtxt(folder/'Job-1_elements.txt',dtype=int)
    mapping = {int(row[0]):index for index,row in enumerate(nodes)}
    connectivity = np.array([[mapping[label] for label in row[1:]] for row in elements])
    points = nodes[:,1:4]
    tetrahedra = points[connectivity]
    rows=[]
    details=[]
    for gauge_id, endpoints in enumerate(metadata,1):
        gauge=[]
        for sign,endpoint in zip([-1,1],endpoints):
            point=np.array(endpoint['point'])
            candidates=np.flatnonzero(np.all(point >= tetrahedra.min(axis=1)-1e-7,axis=1)
                                      & np.all(point <= tetrahedra.max(axis=1)+1e-7,axis=1))
            found=False
            for element_id in candidates:
                vertices=tetrahedra[element_id]
                local=np.linalg.solve((vertices[1:]-vertices[0]).T,point-vertices[0])
                weights=np.r_[1-local.sum(),local]
                if weights.min() >= -1e-7 and weights.max() <= 1+1e-7:
                    for node,weight in zip(connectivity[element_id],weights):
                        rows.append([gauge_id,3*int(node)+2,sign*float(weight)])
                    gauge.append(dict(point=point.tolist(),element=int(elements[element_id,0]),
                                      node_indices=(connectivity[element_id]+1).tolist(),weights=weights.tolist()))
                    found=True
                    break
            if not found:
                raise ValueError('Gauge point is outside the mesh: '+str(point))
        details.append(gauge)
    np.savetxt(folder/'gauge_triplets.csv',rows,delimiter=',',fmt='%.16g')
    (folder/'gauge_metadata.json').write_text(json.dumps(details,indent=2),encoding='utf-8')
    # Independent volume/geometry check before any structural calculation.
    volume=np.abs(np.linalg.det(np.stack([tetrahedra[:,1]-tetrahedra[:,0],tetrahedra[:,2]-tetrahedra[:,0],tetrahedra[:,3]-tetrahedra[:,0]],axis=2))).sum()/6
    if abs(volume-1987500)/1987500 > 1e-7:
        raise ValueError('Mesh volume does not match the 25 mm notched panel')
    return len(nodes),float(volume)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--steps',type=int,default=600)
    args=parser.parse_args()
    package=Path(__file__).resolve().parent
    data=package/'reproducibility/experimental_3d'
    metadata=json.loads((data/'gauge_metadata.json').read_text())
    source=data/'source/damage_static.m'
    results=[]
    for name,seed in [('coarse',12),('medium',9),('fine',6)]:
        folder=args.workspace/name
        folder.mkdir(parents=True,exist_ok=True)
        if (folder/'completion.json').exists():
            results.append(json.loads((folder/'completion.json').read_text()))
            continue
        shutil.copy2(package/'build_nooru_mesh.py',folder/'build_nooru_mesh.py')
        if not (folder/'mesh_metadata.json').exists():
            env=os.environ.copy()
            env['NOORU_SEED_MM']=str(seed)
            command=[shutil.which('abaqus'),'cae','noGUI=build_nooru_mesh.py']
            if os.name=='nt':
                command=['cmd.exe','/d','/c']+command
            with (folder/'build.log').open('w',encoding='utf-8') as stream:
                subprocess.run(command,cwd=folder,env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
        node_count,volume=gauges(folder,metadata)
        create_solver(source,folder/'damage_static.m')
        if name=='coarse':
            subprocess.run([shutil.which('python'),str(package/'run_3d_material_checks.py'),
                            '--workspace',str(folder/'material_checks'),
                            '--source',str(folder/'damage_static.m')],check=True)
        script="""a=readmatrix('gauge_triplets.csv'); G=sparse(a(:,1),a(:,2),a(:,3),4,%d);
maxNumCompThreads(1);
opts=struct('load_path','tension','nIncr',%d,'Uy_end',0.2,'show_live',false,'save_all_increment_geometry',false,'show_mesh',false,'save_show_mesh',false,'print_stride',20,'maxIter',150,'use_line_search',true,'tol',1e-6,'strict_equilibrium',true,'gauge_control',true,'maxLineSearch',12,'gauge_matrix',G,'out_dir',pwd);
damage_static('Job-1',opts);
""" % (3*node_count,args.steps)
        (folder/'run_case.m').write_text(script,encoding='utf-8')
        record=dict(mesh=name,global_seed_mm=seed,initial_intervals=args.steps,final_mean_gauge_mm=0.2,
                    volume_mm3=volume,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    generated_solver_sha256=hashlib.sha256((folder/'damage_static.m').read_bytes()).hexdigest(),
                    equilibrium_tolerance=1e-6,minimum_normalized_interval=1e-7,maximum_rejected_trials=500,
                    history='nondecreasing equivalent strain and damage; commit only converged trials',
                    notch_depth_mm=25,notch_width_mm=5,geometry='200 x 200 x 50 mm panel',
                    material=dict(E_MPa=29000,nu=0.2,ft_MPa=3,GF_N_per_mm=0.11,k=10))
        print('Starting 3D',name,'nodes',node_count,flush=True)
        with (folder/'console.log').open('w',encoding='utf-8') as stream:
            process=subprocess.run(['matlab','-batch','run_case'],cwd=folder,stdout=stream,stderr=subprocess.STDOUT)
        record['return_code']=process.returncode
        record['completed']=process.returncode==0 and (folder/'Job-1_gauge_results.csv').exists()
        (folder/'completion.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
        results.append(record)
        print('3D',name,'completed:',record['completed'],flush=True)
    (args.workspace/'study_manifest.json').write_text(json.dumps(dict(runs=results,
        scope='Published 25 mm notch geometry; strict local-gauge control; target-bisection trials reject uncommitted damage. Failed jobs are excluded.'),indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
