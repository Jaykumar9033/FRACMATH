"""Add solver safeguards without changing the TET4 material routines.

Only residual-reducing corrections are retained. If the Newton direction
fails its line search, try a secant direction and then a scaled negative
gradient of the squared residual. Failed trials still trigger target bisection.
Checkpoints contain only accepted states and can restart the same case.
"""
from pathlib import Path


def safeguard_solver(path):
    path = Path(path)
    text = path.read_text(encoding='utf-8')
    old = '            best_norm = Inf;'
    assert text.count(old) == 1
    text = text.replace(old, '            best_norm = norm0;\n            x_best = x;', 1)
    old = '''            if ~accepted
                x = x_best;
            end'''
    new = '''            if ~accepted && best_norm >= norm0
                % A secant direction is sometimes better at active-set changes.
                [~,Ksec] = residual_and_jac_NR( ...
                    x, Utrial, free, B3, EDOF, Ke_unit3, idx_glob, ...
                    E, nu, k_tc, j0, GF, gradN3, bandwidth_method, history, Fext, ...
                    I_trip,J_trip,eid_rep,Val_unit,ndof,false,V3,gauge_control,Gcontrol,presc_top_uy,Uy_t);
                directions = {-Ksec\\R};
                % Scale the residual-gradient direction by tangent column norms.
                column_scale = max(full(sum(Jff.^2,1)).',1e-20);
                directions{2} = -(Jff.'*R)./column_scale;
                for idir=1:numel(directions)
                    direction=directions{idir};
                    if any(~isfinite(direction)), continue; end
                    alpha=1;
                    for ls=1:maxLineSearch
                        x_try=x+alpha*direction;
                        Rtry=residual_only_NR( ...
                            x_try,Utrial,free,B3,EDOF,Ke_unit3,idx_glob, ...
                            E,nu,k_tc,j0,GF,gradN3,bandwidth_method,history,Fext,ndof,gauge_control,Gcontrol,presc_top_uy,Uy_t);
                        ntry=double(full(norm(Rtry,inf)));
                        if isfinite(ntry) && ntry<best_norm
                            best_norm=ntry; x_best=x_try;
                        end
                        if ntry <= (1-1e-4*alpha)*norm0
                            break;
                        end
                        alpha=alpha/2;
                    end
                    if best_norm<norm0, break; end
                end
            end
            if ~accepted
                if best_norm < norm0
                    x=x_best;
                else
                    fprintf('No residual-reducing correction at target %.9g; rejecting trial.\\n',lambda_load);
                    break;
                end
            end'''
    assert text.count(old) == 1
    text = text.replace(old, new, 1)
    # Save full numerical histories so restarts preserve result rows.
    fields = ['U','history','targets','rejected_trials','delta_s_res','delta_res',
              'Ps_res','P_res','maxD_res','meanD_res','nD005_res','nD050_res',
              'nD950_res','nPlot_res','iter_res','relres_res','mean_h_res',
              'min_h_res','max_h_res','saved_png','gauge_res']
    startup = '''checkpoint_file=fullfile(out_dir,'accepted_checkpoint.mat');
checkpoint_config=[E,nu,j0,GF,k_tc,Uy_end,gamma,nIncr,ne,ndof];
if exist(checkpoint_file,'file')
    restart_state=load(checkpoint_file);
    assert(isequal(restart_state.checkpoint_config,checkpoint_config),'Checkpoint case differs');
'''
    startup += ''.join(f'    {name}=restart_state.{name};\n' for name in fields)
    startup += "    s=restart_state.next_index;\n    [De_bc,~,~,~,h_band_bc]=damage_state_and_internal_force(U,B3,EDOF,Ke_unit3,idx_glob,E,nu,k_tc,j0,GF,gradN3,bandwidth_method,history,ndof);\n    fprintf('Restarting from accepted target %.9g.\\n',targets(s-1));\nend\n"
    old = 'while s <= numel(targets)'
    assert text.count(old) == 1
    text = text.replace(old,startup+old,1)
    saved = "    next_index=s+1;\n    checkpoint_tmp=fullfile(out_dir,'accepted_checkpoint_tmp.mat');\n"
    saved += "    save(checkpoint_tmp," + ','.join("'"+name+"'" for name in fields+['next_index','checkpoint_config']) + ",' -v7');\n"
    saved = saved.replace("' -v7'","'-v7'")
    saved += "    movefile(checkpoint_tmp,checkpoint_file,'f');\n"
    saved += "    writematrix([targets(1:s),relres_res(1:s),iter_res(1:s)],fullfile(out_dir,'accepted_progress.csv'));\n"
    old = '    s = s+1;'
    assert text.count(old) == 1
    text = text.replace(old,saved+old,1)
    # Additional bisections retain the original force-residual tolerance.
    text = text.replace('gap < 1e-7 || rejected_trials >= 500',
                        'gap < 1e-10 || rejected_trials >= 2000',1)
    path.write_text(text,encoding='utf-8')
