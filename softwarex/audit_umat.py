"""Check actual UMAT outputs against an independent material-point calculation.

Preparation writes repeatable cases. Compile umat_point_audit.f90 with the
repository UMAT, run the executable in that workspace, then use --check.
The reference uses a symmetric tensor eigensolve and deviatoric norm.
It checks the documented secant matrix, not a consistent damage tangent.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def reference(row):
    element = int(row[1])
    ex, ey, gamma = row[2:5] + row[5:8]
    old_kappa, old_damage = row[8:10]
    young, poisson, strength, energy, ratio = 37000., .2, 3.5, .09, 10.
    tensor = np.array([[ex, gamma/2], [gamma/2, ey]])
    values, vectors = np.linalg.eigh(tensor)
    normal = vectors[:, -1]
    if abs(ex-ey)+abs(gamma) < 1e-18:
        normal = np.array([1., 0.])
    base_width = [.5, 1., 2., 4.][element-1]
    gradients = np.array([[-1/base_width, -1], [1/base_width, 0], [0, 1]])
    width = 2/np.abs(gradients@normal).sum()
    principal = np.r_[values, -poisson/(1-poisson)*values.sum()]
    invariant1 = principal.sum()
    invariant2 = .5*np.square(principal-principal.mean()).sum()
    equivalent = max(0., (ratio-1)*invariant1/(2*ratio*(1-2*poisson)) +
                     np.sqrt(((ratio-1)/(1-2*poisson))**2*invariant1**2 +
                             12*ratio/(1+poisson)**2*invariant2)/(2*ratio))
    kappa = max(old_kappa, equivalent)
    threshold = strength/young
    final_strain = max(threshold/2+energy/(width*strength), threshold+1e-12)
    damage = 0. if kappa <= threshold else 1-threshold/kappa*np.exp(
        -(kappa-threshold)/(final_strain-threshold))
    damage = min(max(damage, old_damage, 0.), .999999999999)
    elastic = young/(1-poisson**2)*np.array([
        [1, poisson, 0], [poisson, 1, 0], [0, 0, (1-poisson)/2]])
    tangent = (1-damage)*elastic
    stress = tangent@np.array([ex, ey, gamma])
    return np.r_[stress, kappa, damage, width, 1., tangent.flatten(order='F')]


def prepare(folder):
    folder.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20261004)
    cases = []
    for element in range(1, 5):
        for index in range(160):
            strain = rng.normal(0, .0008, 3)
            old = rng.normal(0, .0002, 3)
            history = [rng.uniform(0, .001), rng.uniform(0, .95)]
            cases.append(np.r_[len(cases)+1, element, old, strain-old, history])
        # Zero, nearly isotropic, shear, compression, and split-strain cases.
        for strain in [[0,0,0], [1e-4,1e-4,0], [1e-4,1e-4,1e-19],
                       [0,0,.001], [-.001,.0002,0], [.0003,-.00006,0]]:
            for fraction in [0., .3, 1.]:
                strain = np.asarray(strain)
                cases.append(np.r_[len(cases)+1, element, fraction*strain,
                                   (1-fraction)*strain, 0., 0.])
    rows = np.asarray(cases)
    np.savetxt(folder/'point_inputs.csv', rows, delimiter=',', fmt='%.17g')
    table = [[i, -1/h, -1, 1/h, 0, 0, 1]
             for i, h in enumerate([.5, 1., 2., 4.], 1)]
    np.savetxt(folder/'oliver_t3_gradN.dat', table, fmt='%.17g')
    package = Path(__file__).resolve().parent
    source = package/'reproducibility/2d/solver_main_3pb.m'
    text = source.read_text()
    functions = text[text.index('function [omega_new, kappa_new, h_oliver, strain]'):text.index('function fig_damage')]
    wrapper = """function run_matlab_points()
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
"""
    (folder/'run_matlab_points.m').write_text(wrapper+'\n'+functions)
    (folder/'source.json').write_text(json.dumps(dict(
        matlab_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        method='Local damage functions copied verbatim; only a material-point caller is added.'), indent=2)+'\n')
    print('Prepared', len(rows), 'material-point cases')


def check(folder):
    rows = np.loadtxt(folder/'point_inputs.csv', delimiter=',')
    actual = np.loadtxt(folder/'point_outputs.csv', delimiter=',')
    expected = np.array([reference(row) for row in rows])
    if actual.shape != (len(rows), 17) or not np.array_equal(actual[:,0], rows[:,0]):
        raise ValueError('Missing or reordered material-point outputs')
    difference = np.abs(actual[:,1:]-expected)
    # Absolute plus relative tolerance covers eigensolve and compiler arithmetic.
    allowed = 2e-10+2e-10*np.abs(expected)
    passed = bool(np.isfinite(actual).all() and np.all(difference <= allowed))
    matlab = np.loadtxt(folder/'matlab_point_outputs.csv', delimiter=',')
    matlab_difference = np.abs(matlab[:,1:]-actual[:,4:7])
    matlab_passed = bool(matlab.shape==(len(rows),4) and
                         np.array_equal(matlab[:,0], rows[:,0]) and
                         np.isfinite(matlab).all() and
                         np.all(matlab_difference <= 2e-10+2e-10*np.abs(actual[:,4:7])))
    passed = passed and matlab_passed
    summary = dict(cases=len(rows), passed=passed,
                   maximum_absolute_difference_by_column=difference.max(axis=0).tolist(),
                   matlab_umat_state_width_comparison_passed=matlab_passed,
                   matlab_umat_maximum_absolute_difference=matlab_difference.max(axis=0).tolist(),
                   tolerance='absolute 2e-10 + relative 2e-10',
                   checks=['engineering shear', 'plane-stress strain mapping',
                           'equivalent strain', 'projected width',
                           'irreversible history', 'stress', 'degraded elastic secant matrix',
                           'total strain split across STRAN/DSTRAN', 'eager gradient initialization'],
                   scope='Local CPS3 isothermal small-strain UMAT checks. Does not establish a consistent tangent or general structural convergence.')
    (folder/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))
    if not passed:
        raise SystemExit('UMAT material-point comparison failed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        check(args.workspace)
    else:
        prepare(args.workspace)


if __name__ == '__main__':
    main()
