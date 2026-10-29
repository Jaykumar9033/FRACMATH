function material_checks_3d()
% Local tests of routines extracted unchanged by run_3d_material_checks.py.
% E, nu, ft and GF are the pure-tension experimental comparison settings.
E = 29000;
nu = 0.2;
ft = 3;
GF = 0.11;
k = 10;
eps0 = ft/E;
history_for = @(kappa,omega) struct('kappa',kappa,'omega',omega);
check_rotating_history = true;
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

function s = material_scale(epsv,E,nu,k,j0,GF,gradN,method,history_old)
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


function [B_all,V_el,gradN_all,valid] = precompute_TET4_vectorized(p,T)

ne = size(T,1);

X1 = p(T(:,1),:);
X2 = p(T(:,2),:);
X3 = p(T(:,3),:);
X4 = p(T(:,4),:);

a = X2 - X1;
b = X3 - X1;
c = X4 - X1;

detJ = dot(a, cross(b,c,2), 2);
V_el = abs(detJ)/6;

valid = isfinite(detJ) & abs(detJ) > eps & V_el > eps;

safeDet = detJ;
bad = abs(safeDet) <= eps | ~isfinite(safeDet);
safeDet(bad) = eps;

g2 = cross(b,c,2) ./ safeDet;
g3 = cross(c,a,2) ./ safeDet;
g4 = cross(a,b,2) ./ safeDet;
g1 = -(g2 + g3 + g4);

gx = [g1(:,1), g2(:,1), g3(:,1), g4(:,1)];
gy = [g1(:,2), g2(:,2), g3(:,2), g4(:,2)];
gz = [g1(:,3), g2(:,3), g3(:,3), g4(:,3)];

B_all = zeros(6,12,ne);

for aNode = 1:4
    c0 = 3*(aNode-1);
    gxv = reshape(gx(:,aNode),1,1,ne);
    gyv = reshape(gy(:,aNode),1,1,ne);
    gzv = reshape(gz(:,aNode),1,1,ne);

    B_all(1,c0+1,:) = gxv;
    B_all(2,c0+2,:) = gyv;
    B_all(3,c0+3,:) = gzv;

    B_all(4,c0+1,:) = gyv;
    B_all(4,c0+2,:) = gxv;

    B_all(5,c0+2,:) = gzv;
    B_all(5,c0+3,:) = gyv;

    B_all(6,c0+1,:) = gzv;
    B_all(6,c0+3,:) = gxv;
end

V_el(~valid) = max(V_el(~valid), eps);

gradN_all = zeros(ne,4,3);
gradN_all(:,:,1) = gx;
gradN_all(:,:,2) = gy;
gradN_all(:,:,3) = gz;

end


function h_band = oliver_bandwidth_TET4(gradN_all, crack_n, bandwidth_method)

if nargin < 3 || isempty(bandwidth_method)
    bandwidth_method = "oliver";
end

bandwidth_method = lower(string(bandwidth_method));
if bandwidth_method ~= "oliver"
    warning('Unknown bandwidth_method "%s". Using Oliver directional bandwidth.', char(bandwidth_method));
end

crack_n = double(crack_n);
normal_norm = sqrt(sum(crack_n.^2,2));
bad_normal = ~isfinite(normal_norm) | normal_norm <= 1e-14;
normal_norm(bad_normal) = 1.0;
crack_n = crack_n ./ normal_norm;
crack_n(bad_normal,:) = repmat([1 0 0], nnz(bad_normal), 1);

gx = gradN_all(:,:,1);
gy = gradN_all(:,:,2);
gz = gradN_all(:,:,3);

proj = gx .* crack_n(:,1) + gy .* crack_n(:,2) + gz .* crack_n(:,3);
denom = sum(abs(proj),2);

h_band = 2.0 ./ max(denom, eps);

end


function [eeq, crack_n] = eqv_strain_modified_vm_vec(epsv,nu,k)

exx = reshape(epsv(1,1,:),[],1);
eyy = reshape(epsv(2,1,:),[],1);
ezz = reshape(epsv(3,1,:),[],1);
gxy = reshape(epsv(4,1,:),[],1);
gyz = reshape(epsv(5,1,:),[],1);
gxz = reshape(epsv(6,1,:),[],1);

exy = 0.5*gxy;
eyz = 0.5*gyz;
exz = 0.5*gxz;

I1 = exx + eyy + ezz;
em = I1/3;

dxx = exx - em;
dyy = eyy - em;
dzz = ezz - em;

J2 = 0.5*(dxx.^2 + dyy.^2 + dzz.^2 + 2*(exy.^2 + eyz.^2 + exz.^2));

denom = max(abs(1-2*nu),1e-12);
term1 = ((k-1)/(2*k*denom)) .* I1;

rad = (((k-1)/denom).*I1).^2 + (12*k/((1+nu)^2)).*J2;
rad = max(rad,0);

term2 = (1/(2*k)) .* sqrt(rad);

eeq = max(0, term1 + term2);

[~, crack_n] = max_principal_strain_direction_vec(exx, eyy, ezz, exy, eyz, exz);

end


function [lambda1, n1] = max_principal_strain_direction_vec(exx, eyy, ezz, exy, eyz, exz)

ne = numel(exx);

p1 = exy.^2 + eyz.^2 + exz.^2;
q  = (exx + eyy + ezz) / 3;

p2 = (exx-q).^2 + (eyy-q).^2 + (ezz-q).^2 + 2*p1;
p  = sqrt(max(p2,0) / 6);

p_safe = max(p, eps);
B11 = (exx - q) ./ p_safe;
B22 = (eyy - q) ./ p_safe;
B33 = (ezz - q) ./ p_safe;
B12 = exy ./ p_safe;
B23 = eyz ./ p_safe;
B13 = exz ./ p_safe;

r = 0.5 * (B11.*(B22.*B33 - B23.^2) ...
        - B12.*(B12.*B33 - B23.*B13) ...
        + B13.*(B12.*B23 - B22.*B13));
r = min(max(r,-1),1);
phi = acos(r) / 3;

lambda1 = q + 2*p.*cos(phi);

diag_case = p1 < 1e-28;
spherical = p < 1e-28;

a11 = exx - lambda1;
a22 = eyy - lambda1;
a33 = ezz - lambda1;

row1 = [a11, exy, exz];
row2 = [exy, a22, eyz];
row3 = [exz, eyz, a33];

c12 = cross(row1,row2,2);
c13 = cross(row1,row3,2);
c23 = cross(row2,row3,2);

n12 = sum(c12.^2,2);
n13 = sum(c13.^2,2);
n23 = sum(c23.^2,2);

n1 = c12;
use13 = n13 > n12 & n13 >= n23;
use23 = n23 > n12 & n23 > n13;
n1(use13,:) = c13(use13,:);
n1(use23,:) = c23(use23,:);

nrm = sqrt(sum(n1.^2,2));
bad = ~isfinite(nrm) | nrm < 1e-20 | diag_case | spherical;

if any(bad)
    vals = [exx, eyy, ezz];
    [~, imax] = max(vals, [], 2);
    n_fallback = zeros(ne,3);
    n_fallback(imax == 1,1) = 1;
    n_fallback(imax == 2,2) = 1;
    n_fallback(imax == 3,3) = 1;
    if any(spherical)
        n_fallback(spherical,:) = repmat([1 0 0], nnz(spherical), 1);
    end
    n1(bad,:) = n_fallback(bad,:);
    nrm(bad) = sqrt(sum(n1(bad,:).^2,2));
end

n1 = n1 ./ max(nrm,eps);

end

