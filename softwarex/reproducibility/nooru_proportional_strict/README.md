# Strict proportional mixed-mode attempt

This run uses the original illustrative 20 mm-notch mesh and proportional
gamma=0.6 controls, not the published experimental 4a/4c loading sequence.
It requires relative equilibrium residual <=1e-6 and commits damage only
after convergence. The numerical tangent, line search and trial bisection
follow the verified pure-tension implementation.

The run terminates with return code 1 at normalized target 0.0645837402,
after 81 accepted increments, when the minimum bisection interval is
exhausted. The last trial residual is 1.334e-6. `console.log` and
`completion.json` preserve this failure. There is no complete validated
response CSV, so this run supplies no full-path mixed-mode validation plot.
The tolerance was not relaxed to turn this failure into a pass.

Copy this folder to a separate workspace and run `matlab -batch run_case`
to reproduce the attempted solve. The failure behavior is numerical
evidence, not a successfully completed experiment comparison.
