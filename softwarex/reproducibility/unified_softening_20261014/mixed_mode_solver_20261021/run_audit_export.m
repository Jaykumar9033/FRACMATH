function run_audit_export()
maxNumCompThreads(1);
opts=struct('load_path','4c','nIncr',900,'Uy_end',0.5,'gamma',0.6,'E',29000,'nu',0.2,'ft',3,'GF',0.11,'k',10,'show_live',false,'save_all_increment_geometry',false,'strict_equilibrium',true,'audit_only',true,'out_dir',pwd);
damage_static('Job-1',opts);

end
