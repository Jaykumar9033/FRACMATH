function run_matlab_points()
a=readmatrix('point_inputs.csv'); n=size(a,1);
p=struct('nu',.2,'fc',35,'ft',3.5,'eps0',3.5/37000,'GF',.09, ...
 'OMEGA_MAX',1-1e-12,'regularization','oliver','fixed_width',1.25);
B=repmat([eye(3),zeros(3)],1,1,n);
dofs=reshape(1:6*n,6,n).'; ue=zeros(n,6); ue(:,1:3)=a(:,3:5)+a(:,6:8);
u=reshape(ue.',[],1); widths=[.5;1;2;4]; h=widths(a(:,2));
gradients=[-1./h,-ones(n,1),1./h,zeros(n,2),ones(n,1)];
[damage,kappa,width]=damage_update(u,B,gradients,dofs,a(:,9),a(:,10),p);
writematrix([a(:,1),kappa,damage,width],'matlab_point_outputs.csv');
end

function [omega_new, kappa_new, h_oliver, strain] = damage_update(u, B_all, gradN_all, dof_mat, ...
                                                kappa_old, omega_old, p)
    nE   = size(B_all,3);
    gpu_mode=isa(B_all,'gpuArray');
    if gpu_mode
        u=gpuArray(u);
    end
    u_e  = reshape(u(dof_mat).', 6, 1, nE);
    strain = squeeze(pagemtimes(B_all, u_e)).';
    if gpu_mode
        % One fused element kernel avoids dozens of small GPU launches.
        [og,kg,hg]=arrayfun(@gpu_damage_point,strain(:,1),strain(:,2),strain(:,3), ...
            gradN_all{1},gradN_all{2},gradN_all{3},gradN_all{4},gradN_all{5},gradN_all{6}, ...
            gpuArray(kappa_old),gpuArray(omega_old),p.nu,p.fc/p.ft,p.eps0, ...
            p.GF,p.ft,p.OMEGA_MAX,strcmp(p.regularization,'fixed'),p.fixed_width);
        values=gather([og,kg,hg,strain]);
        omega_new=values(:,1); kappa_new=values(:,2); h_oliver=values(:,3);
        strain=values(:,4:6);
        return;
    end

    ex = strain(:,1); ey = strain(:,2); gxy = strain(:,3);
    me  = (ex+ey)/2;
    rad = sqrt(((ex-ey)/2).^2 + (gxy/2).^2);
    e1  = me + rad;  e2 = me - rad;

    % -----------------------------------------------------------------
    % Full Oliver direction-dependent crack-band width for T3 elements
    % -----------------------------------------------------------------
    % Crack normal n is taken as the maximum principal strain direction.
    % For a 2D strain tensor [ex gxy/2; gxy/2 ey], the principal angle is:
    % theta = 0.5 atan2(gxy, ex-ey).
    theta_p = 0.5 * atan2(gxy, ex - ey);
    nx = cos(theta_p);
    ny = sin(theta_p);

    % If the strain state is almost hydrostatic/isotropic, the principal
    % direction is numerically undefined. Use the x-direction only for those
    % rare cases to keep h finite and stable.
    iso = abs(ex-ey) + abs(gxy) < 1e-18;
    nx(iso) = 1.0;
    ny(iso) = 0.0;

    h_oliver = oliver_bandwidth_T3(gradN_all, nx, ny);
    if strcmp(p.regularization, 'fixed')
        % Ablation: keep one stress-strain softening law for all meshes.
        % No element-dependent fracture-energy rescaling is applied.
        h_oliver(:) = p.fixed_width;
    end

    % Exponential stress-strain softening parameter with Oliver bandwidth.
    % eps_f = eps0/2 + GF/(h_oliver*ft)
    ef_e = max(p.eps0/2 + p.GF ./ (h_oliver * p.ft), p.eps0 + 1e-12);

    % Modified von Mises equivalent strain, using plane-stress out-of-plane
    % principal strain approximation.
    e3  = -(p.nu/(1-p.nu)) .* (e1+e2);
    I1  = e1+e2+e3;
    J2  = (1/6)*((e1-e2).^2 + (e2-e3).^2 + (e3-e1).^2);

    k  = p.fc/p.ft;
    a1 = (k-1)/(2*k*(1-2*p.nu));
    a2 = 1/(2*k);
    a3 = ((k-1)/(1-2*p.nu))^2;
    a4 = 12*k/(1+p.nu)^2;
    eq_s = a1*I1 + a2*sqrt(max(a3*I1.^2 + a4*J2, 0));
    eq_s = max(eq_s, 0);

    kappa_new = max(kappa_old, eq_s);
    omega_new = zeros(nE,1,'like',kappa_new);
    m = kappa_new > p.eps0;
    if any(m)
        km  = kappa_new(m);
        den = max(ef_e(m) - p.eps0, 1e-15);
        omega_new(m) = 1 - (p.eps0 ./ km) .* exp(-(km - p.eps0) ./ den);
    end
    omega_new = max(omega_new, omega_old);
    omega_new = min(max(omega_new,0), p.OMEGA_MAX);
    bad = ~isfinite(omega_new);
    omega_new(bad) = omega_old(bad);
end

function [omega,kappa,h] = gpu_damage_point(ex,ey,gxy,g1x,g1y,g2x,g2y,g3x,g3y, ...
    kappa_old,omega_old,nu,k,eps0,GF,ft,omega_max,fixed,width)
    % Scalar form of the CPU damage update, compiled by gpuArray.arrayfun.
    % Principal strains and crack-normal direction.
    me=(ex+ey)/2;
    rad=sqrt(((ex-ey)/2)^2+(gxy/2)^2);
    e1=me+rad;
    e2=me-rad;
    theta=0.5*atan2(gxy,ex-ey);
    nx=cos(theta);
    ny=sin(theta);
    if abs(ex-ey)+abs(gxy)<1e-18;
        nx=1;
        ny=0;
    end
    % Project each shape-function gradient onto the crack normal.
    den=abs(g1x*nx+g1y*ny)+abs(g2x*nx+g2y*ny)+abs(g3x*nx+g3y*ny);
    h=max(2/max(den,1e-14),1e-12);
    if fixed;
        h=width;
    end
    ef=max(eps0/2+GF/(h*ft),eps0+1e-12);
    e3=-nu/(1-nu)*(e1+e2);
    I1=e1+e2+e3;
    J2=((e1-e2)^2+(e2-e3)^2+(e3-e1)^2)/6;
    a1=(k-1)/(2*k*(1-2*nu));
    a2=1/(2*k);
    a3=((k-1)/(1-2*nu))^2;
    a4=12*k/(1+nu)^2;
    eq=max(a1*I1+a2*sqrt(max(a3*I1^2+a4*J2,0)),0);
    % History and damage cannot decrease on unloading.
    kappa=max(kappa_old,eq);
    omega=0;
    if kappa>eps0
        omega=1-(eps0/kappa)*exp(-(kappa-eps0)/max(ef-eps0,1e-15));
    end
    omega=min(max(max(omega,omega_old),0),omega_max);
    if ~isfinite(omega);
        omega=omega_old;
    end
end

% Project each shape-function gradient onto the strain direction.
% The resulting width scales softening to the given fracture energy.
function h = oliver_bandwidth_T3(gradN_all, nx, ny)
    % Direction-dependent Oliver bandwidth:
    % h(n) = 2 / sum_a |grad(N_a) dot n|, a = 1..3 for T3.
    % gradN_all columns are [g1x g1y g2x g2y g3x g3y].
    g1x = gradN_all(:,1); g1y = gradN_all(:,2);
    g2x = gradN_all(:,3); g2y = gradN_all(:,4);
    g3x = gradN_all(:,5); g3y = gradN_all(:,6);

    den = abs(g1x.*nx + g1y.*ny) + ...
          abs(g2x.*nx + g2y.*ny) + ...
          abs(g3x.*nx + g3y.*ny);

    h = 2.0 ./ max(den, 1e-14);
    h = max(h, 1e-12);
end


% =====================================================================
%          PUBLICATION-QUALITY STATIC FIGURES
% =====================================================================

% ---------------------------------------------------------------------
%  DAMAGE / CRACK FIGURE
% ---------------------------------------------------------------------
