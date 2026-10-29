# Symbols and code names

This reference applies to the current manuscript, its 2D flowchart and the active bending implementations. Plain-text code names represent the mathematical symbols below; they are not different material quantities.

| Quantity | Paper and flowchart | MATLAB | Abaqus UMAT |
|---|---|---|---|
| Damage | d | omega | OMEGA, STATEV(2) |
| Largest equivalent strain | kappa | kappa | KAPPA, STATEV(1) |
| Damage-onset strain | epsilon_0 = f_t/E | p.eps0 | EPS0 |
| Equivalent strain | tilde epsilon | eq_s | EQ |
| Softening strain | epsilon_f | ef_e | EF |
| Selected crack-band width | h | h_oliver | H |
| Fracture energy | G_F | p.GF | GF |
| Young's modulus | E | p.E | E |
| Poisson's ratio | nu | p.nu | ANU |
| Tensile strength | f_t | p.ft | FT |
| Strength ratio | k = f_c/f_t | p.fc/p.ft | FCFT |
| Load increment | m | step (main loop) | controlled by Abaqus |

The manuscript uses m for a load increment, e for an element, and bold n for the crack-normal unit vector. C_0 is the elastic fourth-order tensor; D_0 is its plane-stress matrix representation. The engineering-strain vector is [epsilon_xx, epsilon_yy, gamma_xy], with tensor shear epsilon_xy = gamma_xy/2. K_e^0 is the elastic element stiffness, not the material matrix.

The 2D numerical damage cap is 1 - 1e-12. The 3D cap is 0.999999. These documented numerical settings differ deliberately. These caps are numerical safeguards; they do not define different material damage laws. The current three-point bending, pure-tension, completed mixed-mode and torsion calculations use the same total-tensile-work calibration described below.

The GPU helper uses scalar names eps0, GF, ft and omega_max for the same input quantities. Its local softening variable and equivalent-strain variable follow the same formulas. Archived source snapshots retain the names used when the saved simulations were run.

## Flowchart quantities

The paper introduces the 3D tensor law before its plane-stress specialization. epsilon_V and sigma_V are the engineering-strain and stress vectors used for matrix multiplication in the 2D flowchart. u is nodal displacement, u_final is the final imposed displacement, B_e maps element displacement to engineering strain, A_e is element area, and K_e^0 is undamaged element stiffness. K^- and K^+ denote global stiffness before and after the damage update. r^+ = K^+ u is the internal nodal force vector. Subscripts f and p identify free and prescribed degrees of freedom. eta_m measures the free-force imbalance relative to reactions, using a 1 N lower bound in the denominator. theta is the crack-normal angle, atan2 the two-argument inverse tangent, and d_hat is trial damage. D_sec is the damaged secant material matrix. n_v is the number of element nodes in the general Oliver width (three for T3, four for TET4).

## Common constitutive law and archived illustrations

The current calculations use the same exponential damage law:

    d = 1 - (epsilon_0/kappa) * exp(-(kappa-epsilon_0)/(epsilon_f-epsilon_0))
    epsilon_0 = f_t/E
    epsilon_f = epsilon_0/2 + G_F/(h*f_t)

Damage is zero before its onset, and history and cap checks keep it nondecreasing and below the numerical cap. G_F is total tensile work per unit crack area, including the elastic part. In the 3D sources, `j0` or `eps0` denotes epsilon_0 and `E*j0` denotes f_t.

The paper's `d` is stored as `omega`/`history.omega` in MATLAB and `OMEGA`/`STATEV(2)` in the UMAT. The code names are retained to preserve archived data and interfaces; they represent the same damage variable. The earlier paper notation `omega` and `kappa_0` has been replaced by `d` and `epsilon_0` in the manuscript and native flowchart.

Figure 5(c) deliberately retains the earlier 900-increment mixed-mode montage (steps 29, 37, 41, 53, 75, 127, 275, 407, 900). That earlier run uses post-peak-work calibration and contains unconverged increments. It is a qualitative illustration, not the completed total-work continuation solution. The latter is documented in `reproducibility/unified_softening_20261014/mixed_mode_solver_20261021`. Do not substitute the earlier calibration for the current solver equations.
