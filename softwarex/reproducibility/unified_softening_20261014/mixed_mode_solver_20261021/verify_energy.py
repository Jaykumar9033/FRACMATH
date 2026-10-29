from pathlib import Path
import numpy as np,json
from scipy.io import loadmat
r=Path('.');S=loadmat(r/'audit_state.mat',squeeze_me=True,struct_as_record=False);B=S['B3'];E=float(S['E']);nu=float(S['nu']);V=S['V3'];ed=S['EDOF'].astype(int)-1;Ku=S['Ke_unit3'];ndof=int(S['ndof']);oldU=S['U'];oldd=S['history'].omega
mu=1/(2*(1+nu));la=nu/((1+nu)*(1-2*nu));D=np.diag([la+2*mu]*3+[mu]*3);D[:3,:3]=la;np.fill_diagonal(D[:3,:3],la+2*mu)
def energies(U,d):
 ep=np.einsum('ije,je->ie',B,U[ed]);Y=.5*E*V*np.einsum('ie,ij,je->e',ep,D,ep);return Y,float(np.sum((1-d)*Y))
def forces(U,d):
 f=np.einsum('ije,je->ie',Ku,U[ed])*E*(1-d);F=np.zeros(ndof);np.add.at(F,ed.ravel(order='F'),f.ravel(order='F'));return F
Yold,Psi0=energies(oldU,oldd);Fold=forces(oldU,oldd);work=0.;diss=0.;maxres=0.;minevol=0;trace=[]
fs=sorted((r/'continuation_refined').glob('state_*.mat'))
for f in fs:
 A=loadmat(f,squeeze_me=True,struct_as_record=False);U=A['U'];d=A['history'].omega;Y,Psi=energies(U,d);F=A.get('fi',None)
 if F is None:F=forces(U,d)
 F=np.asarray(F.toarray()).ravel() if hasattr(F,'toarray') else np.asarray(F).ravel()
 work+=.5*np.dot(F+Fold,U-oldU);diss+=np.dot(.5*(Y+Yold),d-oldd);minevol=min(minevol,float(np.min(d-oldd)));oldU=U;oldd=d;Fold=F;Yold=Y;trace.append([float(A['q'][-1]),work,Psi-Psi0,diss,minevol])
if fs:print(json.dumps({'states_checked':len(fs),'last_lambda':float(A['q'][-1]),'min_damage_increment':minevol,'external_work_Nmm':work,'elastic_energy_change_Nmm':Psi-Psi0,'damage_dissipation_Nmm':diss,'energy_balance_relative_error':abs(work-(Psi-Psi0)-diss)/max(abs(work),1e-20)},indent=2))

if trace:np.savetxt(r/'analysis/energy_balance_trace.csv',np.asarray(trace),delimiter=',',header='lambda,external_work_Nmm,elastic_energy_change_Nmm,damage_dissipation_Nmm,minimum_damage_increment',comments='')
