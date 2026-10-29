function run_mixed_mode_continuation(workspace, refine)
% Run the corrected proportional mixed-mode continuation in a separate folder.
% Example: run_mixed_mode_continuation('C:/runs/mixed_mode',true)
% refine=true also runs the half-step numerical sensitivity check.
if nargin<2,refine=false;end
if nargin<1 || isempty(workspace),error('Choose a separate output workspace.');end
here=fileparts(mfilename('fullpath'));
source=fullfile(here,'reproducibility','unified_softening_20261014','mixed_mode_solver_20261021');
if ~isfolder(workspace),mkdir(workspace);end
files={'continuation_solver.m','damage_static.m','run_audit_export.m', ...
       'accepted_checkpoint.mat','verify_analytic_tangent.m'};
meshes=dir(fullfile(source,'Job-1_*.txt'));
files=[files,{meshes.name}];
for i=1:numel(files)
 src=fullfile(source,files{i});dst=fullfile(workspace,files{i});
 if isfile(dst)
  fa=fopen(src,'rb');a=fread(fa,Inf,'*uint8');fclose(fa);
  fb=fopen(dst,'rb');b=fread(fb,Inf,'*uint8');fclose(fb);
  assert(isequal(a,b),'Workspace source differs; use a fresh folder.');
 else
  copyfile(src,dst);
 end
end
previous=pwd;restore=onCleanup(@()cd(previous));cd(workspace);
verify_analytic_tangent;
continuation_solver(struct('out_dir','continuation_full','step_factor',1));
if refine
 continuation_solver(struct('out_dir','continuation_refined','step_factor',0.5));
end
end
