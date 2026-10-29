function run_smoke_checks()

root = fileparts(fileparts(mfilename('fullpath')));

requiredFiles = {
    'README.md'
    'LICENSE'
    'CITATION.cff'
    'CONTRIBUTING.md'
    'CHANGELOG.md'
    'REPRODUCIBILITY.md'
    'doc/theory_manual.tex'
    '3pb/matlab/solver_main_3pb.m'
    '3pb/matlab/Gregoire_3PB/nodes.txt'
    '3pb/matlab/Gregoire_3PB/elements.txt'
    '3pb/matlab/Gregoire_3PB/results/matlab_load_cmod.csv'
    '3pb/abaqus/cdm_umat_2d_OLIVER_T3_FAST.for'
    'softwarex/plot_verified_figures.py'
    'softwarex/reproducibility/results_1000/matlab_load_cmod.csv'
    'softwarex/reproducibility/results_10000/matlab_load_cmod.csv'
    '3pb/abaqus/Gregoire_3PB/results/abaqus_load_cmod.csv'
    'Noor mohammad/Mesh/damage_static.m'
    'Noor mohammad/Mesh/Job-1_nodes.txt'
    'Torsion/working/run_torsion.m'
    'Torsion/working/Job-1_nodes.txt'
    };

for i = 1:numel(requiredFiles)
    path = fullfile(root, requiredFiles{i});
    assert(isfile(path), 'Missing required file: %s', requiredFiles{i});
end

nodes = readmatrix(fullfile(root, '3pb/matlab/Gregoire_3PB/nodes.txt'));
elements = readmatrix(fullfile(root, '3pb/matlab/Gregoire_3PB/elements.txt'));
loadCmod = readmatrix(fullfile(root, '3pb/matlab/Gregoire_3PB/results/matlab_load_cmod.csv'), 'NumHeaderLines', 1);

assert(size(nodes, 1) > 0 && size(nodes, 2) >= 3, '3PB node table has an unexpected shape.');
assert(size(elements, 1) > 0 && size(elements, 2) >= 4, '3PB element table has an unexpected shape.');
assert(size(loadCmod, 1) > 0 && size(loadCmod, 2) >= 2, '3PB load-CMOD table has an unexpected shape.');
assert(max(loadCmod(:, 2)) > 0, '3PB load-CMOD table does not contain positive load values.');
assert(abs(max(loadCmod(:, 2)) - 4026.33) < 1, ...
    'MATLAB CSV does not match the 10,000-step benchmark.');

abaqusCmod = readmatrix(fullfile(root, '3pb/abaqus/Gregoire_3PB/results/abaqus_load_cmod.csv'), 'NumHeaderLines', 1);
assert(abs(max(abaqusCmod(:, 2)) - 3999.14) < 1, ...
    'Abaqus CSV does not match the one-CPU benchmark.');

fprintf('FRACMATH smoke checks passed.\n');
end
