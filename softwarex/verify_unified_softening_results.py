"""Check the published completed unified-softening numerical records."""
from pathlib import Path
import json
import numpy as np
from scipy.io import loadmat

def main():
    root=Path(__file__).resolve().parent/'reproducibility/unified_softening_20261014'
    case=root/'mixed_mode_solver_20261021'
    previous=loadmat(case/'accepted_checkpoint.mat',squeeze_me=True,struct_as_record=False)
    records=[]
    for name in ['continuation_full','continuation_refined']:
        state=loadmat(case/name/'final_state.mat',squeeze_me=True,struct_as_record=False)
        rows=np.atleast_2d(state['rows'])
        assert np.isfinite(state['U']).all() and np.isfinite(rows).all()
        assert abs(float(state['q'][-1])-1)<1e-10
        assert float(rows[:,2].max())<=1e-6
        assert (state['history'].omega>=previous['history'].omega).all()
        assert (state['history'].kappa>=previous['history'].kappa).all()
        assert (state['history'].omega<=.999999+1e-12).all()
        records.append(rows)
    coarse,fine=records
    mask=(fine[:,1]>=coarse[0,1])&(fine[:,1]<=coarse[-1,1])
    err=np.max(abs(fine[mask,6]-np.interp(fine[mask,1],coarse[:,1],coarse[:,6])))/np.max(abs(coarse[:,6]))
    assert err<.01
    audit=loadmat(case/'analytic_tangent_validation.mat',squeeze_me=True)
    assert np.max(audit['errors'])<1e-4
    trace=np.genfromtxt(case/'analysis/energy_balance_trace.csv',delimiter=',',names=True)
    last=trace[-1]
    balance=abs(last['external_work_Nmm']-last['elastic_energy_change_Nmm']-last['damage_dissipation_Nmm'])/abs(last['external_work_Nmm'])
    assert balance<.01 and np.min(trace['minimum_damage_increment'])>=-1e-14
    print(json.dumps(dict(completed=True,max_relative_residuals=[float(x[:,2].max()) for x in records],force_refinement_difference_over_restart_force=float(err),energy_balance_relative_error=float(balance)),indent=2))

if __name__=='__main__':main()
