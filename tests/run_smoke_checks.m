function run_smoke_checks()
root = fileparts(fileparts(mfilename('fullpath')));
mesh = 'softwarex/reproducibility/fixed_increment_extension/medium/Gregoire_3PB/matlab_mesh';
matlabResults = 'softwarex/reproducibility/fixed_increment_extension/medium/reference_matlab_oliver/matlab_load_cmod.csv';
abaqusResults = 'softwarex/reproducibility/fixed_increment_extension/medium/Gregoire_3PB/results/abaqus_load_cmod.csv';
requiredFiles = {
    'README.md'
    'LICENSE'
    'CITATION.cff'
    'REPRODUCIBILITY.md'
    'doc/theory_manual.pdf'
    'softwarex/start_here.m'
    'softwarex/reproducibility/2d/solver_main_3pb.m'
    'softwarex/reproducibility/abaqus/cdm_umat_2d_OLIVER_T3_FAST.for'
    'softwarex/plot_current_figures.py'
    'softwarex/reproducibility/unified_softening_20261014/analysis/summary.json'
    'softwarex/reproducibility/unified_softening_20261014/mixed_mode_solver_20261021/verification_summary.json'
    'softwarex/reproducibility/timing_repeats/analysis/summary.json'
    'Torsion/working/run_torsion.m'
    matlabResults
    abaqusResults
    };
for i = 1:numel(requiredFiles)
    assert(isfile(fullfile(root, requiredFiles{i})), 'Missing file: %s', requiredFiles{i});
end
nodes = readmatrix(fullfile(root, mesh, 'nodes.txt'));
elements = readmatrix(fullfile(root, mesh, 'elements.txt'));
assert(size(nodes,1) > 0 && size(nodes,2) >= 3, 'Invalid node table.');
assert(size(elements,1) > 0 && size(elements,2) >= 4, 'Invalid element table.');
assert(all(ismember(elements(:,2:4),nodes(:,1)), 'all'), 'Connectivity references a missing node.');
m = readmatrix(fullfile(root, matlabResults), 'NumHeaderLines', 1);
a = readmatrix(fullfile(root, abaqusResults), 'NumHeaderLines', 1);
assert(size(m,1) == 2000 && all(isfinite(m), 'all'), 'Invalid MATLAB history.');
assert(size(a,1) == 2001 && all(isfinite(a), 'all'), 'Invalid Abaqus history.');
assert(abs(max(m(:,2))-4205.029) < 1, 'Incorrect MATLAB medium-mesh reference.');
assert(abs(max(a(:,2))-4087.38586) < 1, 'Incorrect Abaqus medium-mesh reference.');
fprintf('FRACMATH smoke checks passed.\n');
end
