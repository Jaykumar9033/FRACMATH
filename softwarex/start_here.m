% START_HERE  Run the paper's 2D MATLAB example from this folder.
% Edit the settings below, then press Run in MATLAB.
% This script calls the same solver used by the paper.

clear;

% 1. Choose settings. Figure 1 uses this medium mesh and 2,000 steps.
number_of_steps = 2000;
number_of_threads = 1;
backend = 'cpu';                 % 'cpu' or 'gpu_hybrid'
show_figures = true;             % false omits live graphics and video
run_material_test = false;       % true checks the material law only

% 2. Locate the supplied solver and mesh. Results go to a separate folder.
package_folder = fileparts(mfilename('fullpath'));
solver_folder = fullfile(package_folder, 'reproducibility', '2d');
mesh_folder = fullfile(package_folder, 'reproducibility', ...
    'fixed_increment_extension', 'medium', 'Gregoire_3PB', 'matlab_mesh');
results_folder = fullfile(package_folder, 'student_results');
addpath(solver_folder);

% 3. Pass the settings to the solver.
% setenv writes a named setting; getenv reads it inside the solver.
% num2str converts a number to the text needed by setenv.
setenv('FRACMATH_CASE_DIR', mesh_folder);
setenv('FRACMATH_RESULTS_DIR', results_folder);
setenv('FRACMATH_STEPS', num2str(number_of_steps));
setenv('FRACMATH_THREADS', num2str(number_of_threads));
setenv('FRACMATH_BACKEND', backend);
setenv('FRACMATH_SIZE_SCALE', '1');
setenv('FRACMATH_MAX_DISP', '-0.1');
setenv('FRACMATH_REGULARIZATION', 'oliver');
setenv('FRACMATH_EQUIVALENT_STRAIN', 'modified_mises');
setenv('FRACMATH_FIXED_WIDTH', '1.25');
setenv('FRACMATH_HEADLESS', num2str(~show_figures));
setenv('FRACMATH_SELFTEST', num2str(run_material_test));

% 4. Run. Numerical results are saved before the final static plots.
solver_main_3pb;
fprintf('Results folder: %s\n', results_folder);
