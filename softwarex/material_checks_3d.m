function material_checks_3d()
% Local tests of routines extracted unchanged by run_3d_material_checks.py.
% E, nu, ft and GF are the pure-tension experimental comparison settings.
E = 29000;
nu = 0.2;
ft = 3;
GF = 0.11;
k = 10;
eps0 = ft/E;
history_for = @(kappa,omega) kappa;
check_rotating_history = false;
directions = [1 0 0; 0 1 0; 0 0 1; 1 1 0; 1 0 1; 0 1 1; 1 1 1; 1 2 3];
directions = directions./sqrt(sum(directions.^2,2));
rows = [];

for edge_length = [0.5 1 2 4]
    points = edge_length*[0 0 0; 1 0 0; 0 1 0; 0 0 1];
    [~,~,gradient,valid] = precompute_TET4_vectorized(points,[1 2 3 4]);
    assert(all(valid), 'Invalid test tetrahedron');
    gradients = squeeze(gradient);
    for direction_id = 1:size(directions,1)
        n = directions(direction_id,:).';
        % Uniaxial stress gives axial strain e and lateral strain -nu*e.
        strain_tensor = n*n.' - nu*(eye(3)-n*n.');
        unit_strain = [strain_tensor(1,1); strain_tensor(2,2); strain_tensor(3,3); ...
                       2*strain_tensor(1,2); 2*strain_tensor(2,3); 2*strain_tensor(1,3)];
        epsv = reshape(2*eps0*unit_strain,6,1,1);
        [eq,normal] = eqv_strain_modified_vm_vec(epsv,nu,k);
        mapping_error = abs(eq/(2*eps0)-1);
        direction_error = 1-abs(normal*n);
        width = oliver_bandwidth_TET4(gradient,normal,'oliver');
        expected_width = 2/sum(abs(gradients*n));
        width_error = abs(width/expected_width-1);

        % In 3D, GF calibrates post-peak work. Stop before the damage cap.
        % Integrate to exponent 4: the analytic finite-interval target is
        % GF*(1-exp(-4)), not the infinite softening integral.
        b = ft*width/GF;
        strains = linspace(eps0,eps0+4/b,10001).';
        epsv = reshape(unit_strain*strains.',6,1,[]);
        repeated_gradient = repmat(gradient,numel(strains),1,1);
        stiffness = material_scale(epsv,E,nu,k,eps0,GF,repeated_gradient,'oliver',history_for(zeros(numel(strains),1),zeros(numel(strains),1)));
        stress = stiffness.*strains;
        energy = width*trapz(strains,stress);
        target = GF*(1-exp(-4));
        energy_error = abs(energy/target-1);
        assert(all(stiffness/E > 1e-6), 'The integration entered the damage cap');

        % Hold the history fixed while unloading in the same direction.
        history = eps0+2/b;
        unloading = [history; history/2];
        epsv = reshape(unit_strain*unloading.',6,1,[]);
        scale = material_scale(epsv,E,nu,k,eps0,GF,repmat(gradient,2,1,1),'oliver',history_for(history*ones(2,1),zeros(2,1)));
        unloading_error = abs(scale(2)/scale(1)-1);
        assert(mapping_error < 1e-10 && direction_error < 1e-10 && width_error < 1e-10);
        assert(energy_error < 1e-6 && unloading_error < 1e-10);
        rows(end+1,:) = [edge_length direction_id width mapping_error direction_error width_error energy target energy_error unloading_error];
    end
end

if check_rotating_history
    % Hold kappa fixed, unload, and rotate the tensile direction. A width
    % change must not undo previously committed damage.
    points = [0 0 0;1 0 0;0 1 0;0 0 1];
    [~,~,gradient,~] = precompute_TET4_vectorized(points,[1 2 3 4]);
    loaded_strain = 0.01;
    first_tensor = loaded_strain*diag([1 -nu -nu]);
    first_eps = reshape([first_tensor(1,1);first_tensor(2,2);first_tensor(3,3);0;0;0],6,1,1);
    first_scale = material_scale(first_eps,E,nu,k,eps0,GF,gradient,'oliver',history_for(0,0));
    saved_damage = 1-first_scale/E;
    for direction_id = 1:size(directions,1)
        n = directions(direction_id,:).';
        tensor = (loaded_strain/2)*(n*n.'-nu*(eye(3)-n*n.'));
        epsv = reshape([tensor(1,1);tensor(2,2);tensor(3,3);2*tensor(1,2);2*tensor(2,3);2*tensor(1,3)],6,1,1);
        scale = material_scale(epsv,E,nu,k,eps0,GF,gradient,'oliver',history_for(loaded_strain,saved_damage));
        assert(1-scale/E >= saved_damage-1e-12, 'Rotating-direction damage decreased');
    end
    fprintf('All eight rotating-direction unloading/history checks passed.\n');
end

% Compression has the tensile equivalent-strain magnitude divided by k.
epsv = reshape([-2*eps0; 2*nu*eps0; 2*nu*eps0; 0; 0; 0],6,1,1);
[eq,~] = eqv_strain_modified_vm_vec(epsv,nu,k);
assert(abs(eq/(2*eps0/k)-1) < 1e-10);
results = array2table(rows,'VariableNames',{'edge_mm','direction_id','width_mm', ...
    'mapping_error','direction_error','width_error','integral_N_per_mm', ...
    'finite_interval_target_N_per_mm','relative_integral_error','unloading_error'});
writetable(results,'material_checks_3d.csv');
fprintf('All %d TET4 size/direction cases and compression mapping passed.\n',size(rows,1));
end
