# Symbols and code names

This reference applies to the current manuscript, its 2D flowchart and the active bending implementations. Plain-text code names represent the mathematical symbols below; they are not different material quantities.

| Quantity | Paper and flowchart | MATLAB | Abaqus UMAT |
|---|---|---|---|
| Damage | omega | omega | OMEGA, STATEV(2) |
| Largest equivalent strain | kappa | kappa | KAPPA, STATEV(1) |
| Damage threshold | kappa_0 = f_t/E | p.eps0 | EPS0 |
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

The 2D numerical damage cap is 1 - 1e-12. The 3D cap is 0.999999. These documented numerical settings differ deliberately. The panel and bending/torsion softening calibrations also differ as explained in the paper; using the same symbols does not make those calibrations identical.

The GPU helper uses scalar names eps0, GF, ft and omega_max for the same input quantities. Its local softening variable and equivalent-strain variable follow the same formulas. Archived source snapshots retain the names used when the saved simulations were run.

## Flowchart quantities

The paper introduces the 3D tensor law before its plane-stress specialization. epsilon_V and sigma_V are the engineering-strain and stress vectors used for matrix multiplication in the 2D flowchart. u is nodal displacement, u_final is the final imposed displacement, B_e maps element displacement to engineering strain, A_e is element area, and K_e^0 is undamaged element stiffness. K^- and K^+ denote global stiffness before and after the damage update. r^+ = K^+ u is the internal nodal force vector. Subscripts f and p identify free and prescribed degrees of freedom. eta_m measures the free-force imbalance relative to reactions, using a 1 N lower bound in the denominator. theta is the crack-normal angle, atan2 the two-argument inverse tangent, and omega_hat is trial damage. D_sec is the damaged secant material matrix. n_v is the number of element nodes in the general Oliver width (three for T3, four for TET4).

One exponential damage law is used throughout. Bending and torsion use epsilon_f = kappa_0/2 + G_F/(h f_t), with G_F including the elastic triangular work. The panel uses epsilon_f = kappa_0 + G_F/(h f_t), with G_F assigned to post-peak work. Its code parameter beta = h f_t/G_F equals 1/(epsilon_f - kappa_0). This is a calibration change, not a second damage law.
