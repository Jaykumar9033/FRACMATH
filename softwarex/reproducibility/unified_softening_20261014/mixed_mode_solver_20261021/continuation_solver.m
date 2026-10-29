function continuation_solver(opts)
if nargin<1,opts=struct;end
if ~isfield(opts,'step_factor'),opts.step_factor=1;end
if ~isfield(opts,'out_dir'),opts.out_dir='continuation_full';end
if ~exist(opts.out_dir,'dir'),mkdir(opts.out_dir);end
maxNumCompThreads(1);
if ~isfile('audit_state.mat'),run_audit_export;end
state=load('audit_state.mat');
E=state.E;
nu=state.nu;
GF=state.GF;
k_tc=state.k_tc;
j0=state.j0;
Uy_end=state.Uy_end;
gamma=state.gamma;
E=state.E;
bandwidth_method=state.bandwidth_method; is4c=state.is4c;
B3=state.B3;
V3=state.V3;
gradN3=state.gradN3;
Ke_unit3=state.Ke_unit3;
ndof=state.ndof;
EDOF=state.EDOF;
idx_glob=state.idx_glob;
I_trip=state.I_trip;
J_trip=state.J_trip;
Val_unit=state.Val_unit;
eid_rep=state.eid_rep;
U=state.U;
history=state.history;
presc_top_uy=state.presc_top_uy;
Lx=state.Lx;
Rx=state.Rx;
base_fix=state.base_fix;
free=state.free;
strict_equilibrium=state.strict_equilibrium;
gauge_control=state.gauge_control;
Gcontrol=state.Gcontrol;
targets=state.targets;
s=state.s;
global FRACMATH_FD_REL FRACMATH_PBOUND;FRACMATH_FD_REL=1e-5;
FRACMATH_PBOUND=zeros(ndof,1);FRACMATH_PBOUND(presc_top_uy)=Uy_end;
FRACMATH_PBOUND(Lx)=.5*gamma*Uy_end;FRACMATH_PBOUND(Rx)=-.5*gamma*Uy_end;
Fext=sparse(ndof,1);n=numel(free);W=[ones(n,1)/n;Uy_end^2];
elem=8038;ep0=B3(:,:,elem)*U(EDOF(:,elem));
[~,nn]=eqv_strain_modified_vm_vec(reshape(ep0,6,1,1),nu,k_tc);h0=oliver_bandwidth_TET4(gradN3(elem,:,:),nn,bandwidth_method);
proj=[nn(1)^2 nn(2)^2 nn(3)^2 nn(1)*nn(2) nn(2)*nn(3) nn(1)*nn(3)];
G=sparse(1,ndof);G(EDOF(:,elem))=h0*proj*B3(:,:,elem);
C=[G(free),G*FRACMATH_PBOUND];
q=[U(free);targets(s-1)];qprev=q;step=1e-5;maxstep=1e-3;minstep=1e-9;
fprintf('Initial gauge opening %.9g mm\n',G*U);save(fullfile(opts.out_dir,'opening_gauge.mat'),'G','elem','h0','nn');
[A,J,F,L]=evalq(q);v=[-J\L;1];v=v/(C*v);t=v;
accepted=0;rejected=0;rows=[];checkpoint=fullfile(opts.out_dir,'checkpoint.mat');
restarting=exist(checkpoint,'file')~=0;
if restarting
 A=load(checkpoint);q=A.q;U=A.U;history=A.history;rows=A.rows;t=A.t;step=A.step;accepted=A.accepted;rejected=A.rejected;
end
if ~restarting,step=step*opts.step_factor;end
maxstep=maxstep*opts.step_factor;

while q(end)<1-1e-12 && accepted<5000
 q0=q;Cstep=C;increment=step;endpoint=false;
 if t(end)>0 && q(end)+step*t(end)>=1
  Cstep=sparse(1,n+1);Cstep(end)=1;increment=1-q(end);endpoint=true;
  qtry=q+increment*t/t(end);
 else
  qtry=q+step*t;
 end
 ok=false;
 for it=1:50
  [R,J,F,L]=evalq(qtry);scale=max(1,norm(F,inf));rr=norm(R,inf)/scale;
  g=Cstep*(qtry-q0)-increment;
  if mod(it,5)==1,fprintf('ARC trial %d step %.3e it %d lambda %.10f res %.4e\n',accepted+1,step,it,qtry(end),rr);end
  if rr<=1e-6 && abs(g)<=1e-8*abs(increment),ok=true;break;end
  row=Cstep;M=[J,sparse(L);sparse(1e6*row)];rhs=[R;1e6*g];dq=full(-M\full(rhs));
  best=norm([R/scale;g/increment]);alpha=1;improved=false;
  for ls=1:24
   qc=qtry+alpha*dq;[rc,~,fc]=evalq(qc,false);gc=Cstep*(qc-q0)-increment;
   merit=norm([rc/scale;gc/increment]);
   if merit<(1-1e-4*alpha)*best,qtry=qc;improved=true;break;end
   alpha=alpha/2;
  end
  if ~improved,break;end
 end
 if ~ok
  step=step/2;rejected=rejected+1;fprintf('ARC REJECT res %.5e step now %.3e\n',rr,step);
  if step<minstep,error('Arc step exhausted');end
  continue;
 end
 q=full(qtry);U=FRACMATH_PBOUND*q(end);U(free)=q(1:n);
 [dam,~,fi,eq,h]=damage_state_and_internal_force(U,B3,EDOF,Ke_unit3,idx_glob,E,nu,k_tc,j0,GF,gradN3,bandwidth_method,history,ndof);
 previous_history=history;
 history.kappa=max(history.kappa,eq);history.omega=max(history.omega,dam);
 assert(all(history.kappa>=previous_history.kappa) && all(history.omega>=previous_history.omega),'History decreased');
 [R,J,F,L]=evalq(q);post=norm(R,inf)/max(1,norm(F,inf));assert(post<=1e-6,'Commit residual changed');
 accepted=accepted+1;rows(end+1,:)=[accepted,q(end),post,it,step,max(dam),full(sum(fi(presc_top_uy))),full(sum(fi(Lx))),full(G*U),min(history.omega),endpoint];
 tangent=q-q0;t=tangent/(C*tangent);
 fprintf('ARC ACCEPT %d lambda %.10f res %.4e maxD %.6f P %.3f\n',accepted,q(end),post,max(dam),full(sum(fi(presc_top_uy))));
 save(checkpoint,'q','U','history','rows','t','step','accepted','rejected','opts');
 writematrix(rows,fullfile(opts.out_dir,'accepted_progress.csv'));
 save(fullfile(opts.out_dir,sprintf('state_%05d.mat',accepted)),'U','history','q','rows','fi','h','eq','dam');
 if it<7,step=min(maxstep,step*1.3);elseif it>20,step=step*.7;end
end
assert(abs(q(end)-1)<1e-10,'Loading endpoint not reached');
 writematrix(rows,fullfile(opts.out_dir,'results.csv'));
 save(fullfile(opts.out_dir,'final_state.mat'),'U','history','q','rows','G','opts');
 fprintf('FULL MIXED-MODE LOADING PATH COMPLETED.\n');
 function [R,J,F,L]=evalq(qq,needjac)
 if nargin<2,needjac=true;end
 Ut=FRACMATH_PBOUND*qq(end);
 if needjac
  [R,J,F,L]=residual_and_jac_NR(qq(1:n),Ut,free,B3,EDOF,Ke_unit3,idx_glob,E,nu,k_tc,j0,GF,gradN3,bandwidth_method,history,Fext,I_trip,J_trip,eid_rep,Val_unit,ndof,true,V3,false,Gcontrol,presc_top_uy,qq(end)*Uy_end);
 else
  Ut(free)=qq(1:n);[~,~,F]=damage_state_and_internal_force(Ut,B3,EDOF,Ke_unit3,idx_glob,E,nu,k_tc,j0,GF,gradN3,bandwidth_method,history,ndof);R=F(free);J=[];L=[];
 end
 end
end
function [R,Jff,Fint,Jload] = residual_and_jac_NR( ...
    x, Utrial, free, B3, EDOF, Ke_unit3, idx_glob, ...
    E, nu, k_tc, j0, GF, gradN3, bandwidth_method, history, Fext, ...
    I_trip, J_trip, eid_rep, Val_unit, ndof, strict_equilibrium, V3, gauge_control,Gcontrol,presc_top_uy,Uy_t)

Uloc = Utrial;
Uloc(free) = x(1:numel(free));
if gauge_control, Uloc(presc_top_uy)=x(end); end

[~, s_e, Fint, ~] = damage_state_and_internal_force( ...
    Uloc, B3, EDOF, Ke_unit3, idx_glob, E, nu, k_tc, j0, GF, gradN3, bandwidth_method, history, ndof);

Rfull = Fint - Fext;
R = Rfull(free);
if gauge_control, R=[R;1e6*(Gcontrol*Uloc-Uy_t)]; end

vals = Val_unit .* s_e(eid_rep);
K = sparse(I_trip, J_trip, vals, ndof, ndof);
if strict_equilibrium
    % Differentiate the same constitutive update; no fitted material terms.
    ne=size(EDOF,2);epsv=pagemtimes(B3,reshape(Uloc(EDOF),12,1,ne));
    ds=analytic_scale_derivative(epsv,E,nu,k_tc,j0,GF,gradN3,history);
    [Dunit,~,~]=iso3D_D(1,nu);
    v=pagemtimes(permute(B3,[2,1,3]),pagemtimes(Dunit,epsv));
    q=pagemtimes(ds,B3);
    correction=bsxfun(@times,pagemtimes(v,q),reshape(V3,1,1,ne));
    K=K+sparse(I_trip,J_trip,correction(:),ndof,ndof);
else
    K = 0.5*(K + K.');
end

global FRACMATH_PBOUND;
Jload=K(free,:)*FRACMATH_PBOUND;
Jff = K(free,free);
if gauge_control
    Jff=[Jff,sum(K(free,presc_top_uy),2);1e6*Gcontrol(free),1e6*sum(Gcontrol(presc_top_uy))];
end

if ~isempty(Jff)
    dmax = double(full(max(abs(diag(Jff)))));
    if isempty(dmax) || dmax <= 0 || ~isfinite(dmax)
        dmax = 1.0;
    end
    Jff = Jff + speye(size(Jff))*1e-12*dmax;
end

end

function R = residual_only_NR( ...
    x, Utrial, free, B3, EDOF, Ke_unit3, idx_glob, ...
    E, nu, k_tc, j0, GF, gradN3, bandwidth_method, history, Fext, ndof,gauge_control,Gcontrol,presc_top_uy,Uy_t)

Uloc = Utrial;
Uloc(free) = x(1:numel(free));
if gauge_control, Uloc(presc_top_uy)=x(end); end

[~, ~, Fint, ~] = damage_state_and_internal_force( ...
    Uloc, B3, EDOF, Ke_unit3, idx_glob, E, nu, k_tc, j0, GF, gradN3, bandwidth_method, history, ndof);

Rfull = Fint - Fext;
R = Rfull(free);
if gauge_control, R=[R;1e6*(Gcontrol*Uloc-Uy_t)]; end

end

function [De, s_e, Fint, eeq, h_band, crack_n] = damage_state_and_internal_force( ...
    U, B3, EDOF, Ke_unit3, idx_glob, E, nu, k_tc, j0, GF, gradN3, bandwidth_method, history_old, ndof)

ne = size(EDOF,2);

ue12 = reshape(U(EDOF), 12, 1, ne);
epsv = pagemtimes(B3, ue12);

[eeq, crack_n] = eqv_strain_modified_vm_vec(epsv, nu, k_tc);
eeq = reshape(eeq, [], 1);

h_band = oliver_bandwidth_TET4(gradN3, crack_n, bandwidth_method);
% GF is total tensile work per crack area, including the elastic part.
ef = max(j0/2 + GF./(h_band(:)*(E*j0)), j0+1e-12);
be = 1./(ef-j0);

kappa_trial = max(history_old.kappa, eeq);

De = zeros(ne,1);
active = kappa_trial >= j0;
De(active) = 1 - (j0 ./ kappa_trial(active)) .* exp(-be(active) .* (kappa_trial(active)-j0));
De = max(min(max(De,0),0.999999), history_old.omega);

s_e = E .* max(1 - De, 1e-8);

fe12 = pagemtimes(Ke_unit3, ue12);
fe12 = bsxfun(@times, fe12, reshape(s_e,1,1,ne));

Fint = assemble_accum(idx_glob, fe12, ndof);

end

function s = material_scale(epsv,E,nu,k,j0,GF,gradN,method,history_old)
[eeq,n] = eqv_strain_modified_vm_vec(epsv,nu,k);
h = oliver_bandwidth_TET4(gradN,n,method);
kappa_trial = max(history_old.kappa,reshape(eeq,[],1));
damage = zeros(size(kappa_trial));
active = kappa_trial>=j0;
ef = max(j0/2 + GF./(h(:)*(E*j0)), j0+1e-12);
b = 1./(ef-j0);
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

function EDOF = build_edof(T)

ne = size(T,1);
EDOF = zeros(12,ne);

for a = 1:4
    rows = 3*(a-1) + (1:3);
    n = T(:,a).';
    EDOF(rows(1),:) = 3*n - 2;
    EDOF(rows(2),:) = 3*n - 1;
    EDOF(rows(3),:) = 3*n;
end

end

function [I_trip, J_trip, Val_unit, eid_rep] = build_triplet_pattern(EDOF, Ke_unit3)

ne = size(EDOF,2);

I_blk = repmat(EDOF, 12, 1);
J_blk = repelem(EDOF, 12, 1);

I_trip = I_blk(:);
J_trip = J_blk(:);

Val_pages = reshape(Ke_unit3, 144, ne);
Val_unit = Val_pages(:);

eid_rep = repelem((1:ne)', 144);

end

function [D,lambda,mu] = iso3D_D(E,nu)

mu = E/(2*(1+nu));
lambda = E*nu/((1+nu)*(1-2*nu));

D = [lambda+2*mu, lambda,      lambda,      0,  0,  0;
     lambda,      lambda+2*mu, lambda,      0,  0,  0;
     lambda,      lambda,      lambda+2*mu, 0,  0,  0;
     0,           0,           0,           mu, 0,  0;
     0,           0,           0,           0,  mu, 0;
     0,           0,           0,           0,  0,  mu];

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

function F = assemble_accum(idx_glob, fe12, ndof)

F = accumarray(idx_glob(:), fe12(:), [ndof,1], @sum, 0, true);

end

function [did_save, png_name] = save_damage_geometry_snapshot( ...
    fig, ax, hHull, hDam, p, U, def_scale, allF, owner_per_face, De, ...
    plot_thr, inc, nIncr, lambda_load, out_folder, prefix, image_res, save_when_empty, show_mesh_in_saved, damage_clim, damage_clim_mode)

if nargin < 19 || isempty(show_mesh_in_saved)
    show_mesh_in_saved = true;
end
if nargin < 20 || isempty(damage_clim)
    damage_clim = [0 1];
end
if nargin < 21 || isempty(damage_clim_mode)
    damage_clim_mode = "visible";
end

face_damage = De(owner_per_face);
keep_faces = face_damage >= plot_thr;
nfaces = nnz(keep_faces);

did_save = false;
png_name = '';

if nfaces == 0 && ~save_when_empty
    return;
end

oldHullVis = '';
oldClim = get_current_clim(ax);

Ux = U(1:3:end);
Uy = U(2:3:end);
Uz = U(3:3:end);
P_def = p + def_scale*[Ux,Uy,Uz];

if nargin >= 3 && ~isempty(hHull) && isgraphics(hHull)
    oldHullVis = get(hHull,'Visible');
    set(hHull,'Vertices',P_def);
    if show_mesh_in_saved
        set(hHull,'Visible','on');
    else
        set(hHull,'Visible','off');
    end
end

if nfaces > 0
    crack_faces = allF(keep_faces,:);
    crack_colors = face_damage(keep_faces);

    set(hDam, ...
        'Vertices', P_def, ...
        'Faces', crack_faces, ...
        'FaceVertexCData', crack_colors, ...
        'Visible','on');
else
    set(hDam, ...
        'Vertices', P_def, ...
        'Faces', zeros(0,3), ...
        'FaceVertexCData', zeros(0,1), ...
        'Visible','off');
end

if nfaces > 0
    apply_damage_color_limits(ax, face_damage(keep_faces), plot_thr, damage_clim, damage_clim_mode);
else
    apply_damage_color_limits(ax, [], plot_thr, damage_clim, damage_clim_mode);
end

title(ax, sprintf('Damage with mesh | inc=%d/%d | lambda=%.4f | damaged faces=%d | omega >= %.3f', ...
    inc, nIncr, lambda_load, nfaces, plot_thr), ...
    'FontSize',12,'FontWeight','bold','Interpreter','none');

view(ax,2);
camproj(ax,'orthographic');
camup(ax,[0 1 0]);
drawnow;

png_name = fullfile(out_folder, sprintf('%s_inc_%04d_damageMesh_omega_ge_%s.png', ...
    prefix, inc, fmt_underscore(plot_thr)));

exportgraphics(fig, png_name, 'Resolution', image_res);

if ~isempty(oldHullVis) && isgraphics(hHull)
    set(hHull,'Visible',oldHullVis);
end

if ~isempty(oldClim)
    set_current_clim(ax, oldClim);
end

did_save = true;

end

function update_damage_geometry_live( ...
    fig, ax, hHull, hDam, p, U, def_scale, allF, owner_per_face, De, ...
    live_thr, inc, nIncr, lambda_load, maxD, nLive, show_mesh_live, damage_clim, damage_clim_mode)

if nargin < 17 || isempty(show_mesh_live)
    show_mesh_live = true;
end
if nargin < 18 || isempty(damage_clim)
    damage_clim = [0 1];
end
if nargin < 19 || isempty(damage_clim_mode)
    damage_clim_mode = "visible";
end

if ~isgraphics(fig) || ~isgraphics(ax) || ~isgraphics(hDam)
    return;
end

face_damage = De(owner_per_face);
keep_faces = face_damage >= live_thr;
nfaces = nnz(keep_faces);

Ux = U(1:3:end);
Uy = U(2:3:end);
Uz = U(3:3:end);
P_def = p + def_scale*[Ux,Uy,Uz];

if ~isempty(hHull) && isgraphics(hHull)
    set(hHull, 'Vertices', P_def, 'Visible', ternary_vis(show_mesh_live));
end

if nfaces > 0
    set(hDam, ...
        'Vertices', P_def, ...
        'Faces', allF(keep_faces,:), ...
        'FaceVertexCData', face_damage(keep_faces), ...
        'Visible','on');
else
    set(hDam, ...
        'Vertices', P_def, ...
        'Faces', zeros(0,3), ...
        'FaceVertexCData', zeros(0,1), ...
        'Visible','off');
end

if nfaces > 0
    apply_damage_color_limits(ax, face_damage(keep_faces), live_thr, damage_clim, damage_clim_mode);
else
    apply_damage_color_limits(ax, [], live_thr, damage_clim, damage_clim_mode);
end

title(ax, sprintf('LIVE damage + mesh | inc=%d/%d | lambda=%.4f | maxD=%.4f | N(omega >= %.3f)=%d | faces=%d', ...
    inc, nIncr, lambda_load, maxD, live_thr, nLive, nfaces), ...
    'FontSize',12,'FontWeight','bold','Interpreter','none');

view(ax,2);
camproj(ax,'orthographic');
camup(ax,[0 1 0]);

end

function extFaces = external_hull(T)

allF = [T(:,[1 2 3]); T(:,[1 2 4]); T(:,[1 3 4]); T(:,[2 3 4])];
sF = sort(allF,2);
[uf,~,ic] = unique(sF,'rows');
cnt = accumarray(ic,1);
extFaces = uf(cnt == 1,:);

end

function try_set(h, prop, val)

if isempty(h) || ~isgraphics(h)
    return;
end

try
    set(h, prop, val);
catch

end

end

function v = ternary_vis(tf)

if tf
    v = 'on';
else
    v = 'off';
end

end

function nodes = read_nodeset_local(file_name, ids, set_name)

raw = readmatrix(file_name);
raw = raw(:);
raw = raw(isfinite(raw));

[tf,loc] = ismember(raw, ids);
if any(~tf)
    warning('%d nodes in %s set were not found in nodes file and were ignored.', nnz(~tf), set_name);
end

nodes = uint32(loc(tf));
nodes = nodes(nodes > 0);

end

function m = safe_mean(x)

if isempty(x)
    m = NaN;
else
    m = double(full(mean(x)));
end

end

function c = full_damage_cmap()

n = 256;
stops = [0.15 0.20 0.85;
         0.00 0.70 0.90;
         0.12 0.80 0.30;
         0.98 0.90 0.05;
         0.98 0.45 0.03;
         0.82 0.04 0.04];

pos = [0, 0.25, 0.50, 0.75, 0.90, 1.00];

t = linspace(0,1,n).';
c = zeros(n,3);

for ch = 1:3
    c(:,ch) = interp1(pos, stops(:,ch), t, 'pchip');
end

c = min(max(c,0),1);

end

function c = select_damage_cmap(name, n_bands, make_discrete)

if nargin < 1 || isempty(name)
    name = 'turbo';
end
if nargin < 2 || isempty(n_bands)
    n_bands = 12;
end
if nargin < 3 || isempty(make_discrete)
    make_discrete = false;
end

name = lower(string(name));
n = 256;

switch name
    case "turbo"
        c = builtin_colormap_safe('turbo', n);
    case "parula"
        c = builtin_colormap_safe('parula', n);
    case "jet"
        c = builtin_colormap_safe('jet', n);
    case "hot"
        c = builtin_colormap_safe('hot', n);
    case "cool"
        c = builtin_colormap_safe('cool', n);
    case "spring"
        c = builtin_colormap_safe('spring', n);
    case "autumn"
        c = builtin_colormap_safe('autumn', n);
    case "winter"
        c = builtin_colormap_safe('winter', n);
    case "fire"
        c = interp_colormap([ ...
            0.02 0.02 0.08;
            0.15 0.05 0.40;
            0.80 0.05 0.05;
            1.00 0.55 0.00;
            1.00 0.95 0.05], n);
    case "yellow_red"
        c = interp_colormap([ ...
            1.00 1.00 0.75;
            1.00 0.85 0.05;
            1.00 0.45 0.00;
            0.85 0.05 0.02;
            0.35 0.00 0.00], n);
    case "blue_green_yellow_red"
        c = interp_colormap([ ...
            0.05 0.10 0.75;
            0.00 0.70 0.85;
            0.10 0.75 0.25;
            1.00 0.92 0.05;
            1.00 0.42 0.00;
            0.80 0.00 0.00], n);
    case "damage_bands"
        c = interp_colormap([ ...
            0.05 0.15 0.95;
            0.00 0.70 1.00;
            0.00 0.75 0.20;
            0.95 0.95 0.05;
            1.00 0.50 0.00;
            0.90 0.00 0.00;
            0.35 0.00 0.00], max(n_bands,2));
        return;
    otherwise
        warning('Unknown damage_colormap "%s". Using turbo.', char(name));
        c = builtin_colormap_safe('turbo', n);
end

if make_discrete
    c = discretize_colormap(c, n_bands);
end

end

function c = builtin_colormap_safe(name, n)

try
    f = str2func(char(name));
    c = f(n);
catch
    if strcmpi(char(name),'turbo')
        c = jet(n);
    else
        c = full_damage_cmap();
    end
end

end

function c = interp_colormap(stops, n)

m = size(stops,1);
pos = linspace(0,1,m);
t = linspace(0,1,n).';
c = zeros(n,3);

for ch = 1:3
    c(:,ch) = interp1(pos, stops(:,ch), t, 'pchip');
end

c = min(max(c,0),1);

end

function c = discretize_colormap(c0, n_bands)

n_bands = max(2, round(n_bands));
idx = round(linspace(1, size(c0,1), n_bands));
c = c0(idx,:);

end

function apply_damage_color_limits(ax, visible_damage, threshold, default_clim, mode)

mode = lower(string(mode));

switch mode
    case "full"
        lim = default_clim;

    case "visible"
        lim = [threshold, default_clim(2)];

    case "auto"
        visible_damage = visible_damage(isfinite(visible_damage));
        if isempty(visible_damage)
            lim = default_clim;
        else
            dmin = min(visible_damage);
            dmax = max(visible_damage);
            if abs(dmax - dmin) < 1e-8
                dmin = max(0, dmin - 0.025);
                dmax = min(1, dmax + 0.025);
            end
            lim = [dmin, dmax];
        end

    otherwise
        lim = [threshold, default_clim(2)];
end

if numel(lim) ~= 2 || any(~isfinite(lim)) || lim(2) <= lim(1)
    lim = [0 1];
end

lim(1) = max(0, lim(1));
lim(2) = min(1, lim(2));
if lim(2) <= lim(1)
    lim = [0 1];
end

set_current_clim(ax, lim);

end

function lim = get_current_clim(ax)

try
    lim = clim(ax);
catch
    lim = caxis(ax);
end

end

function set_current_clim(ax, lim)

try
    clim(ax, lim);
catch
    caxis(ax, lim);
end

end

function val = local_get(opts, field, default)

if isstruct(opts) && isfield(opts,field) && ~isempty(opts.(field))
    val = opts.(field);
else
    val = default;
end

end

function s = fmt_underscore(x)

s = sprintf('%.4e', x);
s = strrep(s, '+', '');
s = strrep(s, '-', 'm');
s = strrep(s, '.', 'p');

end

function s=branch_scale(epsv,E,nu,k,j0,GF,gradN,method,history,loading)
[eeq,n]=eqv_strain_modified_vm_vec(epsv,nu,k);h=oliver_bandwidth_TET4(gradN,n,method);
kk=history.kappa;eeq=eeq(:);kk(loading)=eeq(loading);kk=max(kk,j0);
ef=max(j0/2+GF./(h(:)*(E*j0)),j0+1e-12);
s=E*j0./kk.*exp(-(kk-j0)./(ef-j0));
end

function ds=analytic_scale_derivative(ep,E,nu,k,j0,GF,gradN,history)
ne=size(ep,3);ev=reshape(ep,6,ne).';xx=ev(:,1);yy=ev(:,2);zz=ev(:,3);xy=ev(:,4)/2;yz=ev(:,5)/2;xz=ev(:,6)/2;
[eq,n]=eqv_strain_modified_vm_vec(ep,nu,k);eq=eq(:);
[lam,~]=max_principal_strain_direction_vec(xx,yy,zz,xy,yz,xz);
I1=xx+yy+zz;dev=ev(:,1:3)-I1/3;J2=.5*sum(dev.^2,2)+xy.^2+yz.^2+xz.^2;
AA=(k-1)/(2*k*(1-2*nu));BB=((k-1)/(1-2*nu))^2;CC=12*k/(1+nu)^2;
rad=sqrt(max(BB*I1.^2+CC*J2,0));di=repmat([1 1 1 0 0 0],ne,1);dJ=[dev,xy,yz,xz];
deq=AA*di+(2*BB*I1.*di+CC*dJ)./(4*k*max(rad,realmin));deq(eq<=0,:)=0;
A=zeros(3,3,ne);A(1,1,:)=xx;A(2,2,:)=yy;A(3,3,:)=zz;A(1,2,:)=xy;A(2,1,:)=xy;A(2,3,:)=yz;A(3,2,:)=yz;A(1,3,:)=xz;A(3,1,:)=xz;
nc=reshape(n.',3,1,ne);M=-A;
for j=1:3,M(j,j,:)=M(j,j,:)+reshape(lam,1,1,ne);end
M=M+j0*pagemtimes(nc,permute(nc,[2 1 3]));
Q=zeros(3,6,ne);Q(1,1,:)=n(:,1);Q(2,2,:)=n(:,2);Q(3,3,:)=n(:,3);
Q(1,4,:)=n(:,2)/2;Q(2,4,:)=n(:,1)/2;Q(2,5,:)=n(:,3)/2;Q(3,5,:)=n(:,2)/2;Q(1,6,:)=n(:,3)/2;Q(3,6,:)=n(:,1)/2;
rhs=Q-pagemtimes(nc,pagemtimes(permute(nc,[2 1 3]),Q));
% Derivative is unused in undamaged spherical states; make their auxiliary systems invertible.
bad=abs(lam-xx)+abs(lam-yy)+abs(lam-zz)+abs(xy)+abs(yz)+abs(xz)<1e-15;
M(:,:,bad)=repmat(eye(3)*j0,1,1,nnz(bad));
dn=pagemldivide(M,rhs);
proj=gradN(:,:,1).*n(:,1)+gradN(:,:,2).*n(:,2)+gradN(:,:,3).*n(:,3);
den=sum(abs(proj),2);a=max(GF*den/(2*(E*j0))-j0/2,1e-12);
g=sum(gradN.*reshape(sign(proj),ne,4,1),2);g=reshape(g,ne,3);
dden=reshape(pagemtimes(reshape(g.',1,3,ne),dn),6,ne).';
da=GF/(2*(E*j0))*dden;da(a<=1e-12,:)=0;
kap=max(history.kappa,eq);dk=deq;dk(eq<=history.kappa,:)=0;
raws=E*j0./kap.*exp(-(kap-j0)./a);rawd=1-raws/E;
active=kap>j0 & rawd>history.omega & rawd<0.999999;
dsv=raws.*(-(1./kap+1./a).*dk+(kap-j0)./a.^2.*da);dsv(~active,:)=0;
ds=reshape(dsv.',1,6,ne);
end
