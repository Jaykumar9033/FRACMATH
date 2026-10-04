a=readmatrix('gauge_triplets.csv'); G=sparse(a(:,1),a(:,2),a(:,3),4,54540);
maxNumCompThreads(1);
opts=struct('load_path','tension','nIncr',600,'Uy_end',0.2,'show_live',false,'save_all_increment_geometry',false,'show_mesh',false,'save_show_mesh',false,'print_stride',20,'maxIter',150,'use_line_search',true,'tol',1e-6,'strict_equilibrium',true,'gauge_control',true,'maxLineSearch',12,'gauge_matrix',G,'out_dir',pwd);
damage_static('Job-1',opts);
