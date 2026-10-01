! Standalone material-point verification linked to the unmodified repository UMAT.
! GETOUTDIR is a test-only stub; actual Abaqus supplies that utility.
program material_check
  implicit none
  integer :: i,j,k,jstep(4),el
  real(8) :: widths(4),h,eps0,ef,decay,e,last_e,last_s,G,o_commit,k_commit,ratio
  real(8) :: angles(4),angle,nx,ny,h_projected,s_projected,pi
  real(8) :: stress(3), statev(4), dds(3,3), sse,spd,scd,rpl
  real(8) :: ddsdt(3),drplde(3),drpldt,strain(3),dstrain(3),t(2),dt
  real(8) :: temp,dtemp,predef(1),dpred(1),props(5),coords(3),drot(3,3)
  real(8) :: pnewdt,celent,f0(3,3),f1(3,3)
  character(80) :: cmname
  widths=[.5d0,1.d0,2.d0,4.d0]
  props=[37000.d0,.2d0,3.5d0,.09d0,10.d0]
  eps0=props(3)/props(1)
  pi=acos(-1.d0);angles=[15.d0,45.d0,75.d0,90.d0];nx=1;ny=0
  stress=0;statev=0;dds=0;sse=0;spd=0;scd=0;rpl=0
  ddsdt=0;drplde=0;drpldt=0;strain=0;dstrain=0;t=0;dt=.001d0
  temp=0;dtemp=0;predef=0;dpred=0;coords=0;drot=0;pnewdt=1;celent=99
  f0=0;f1=0;jstep=[1,1,0,0];cmname='CONCRETE'
  open(88,file='oliver_t3_gradN.dat',status='replace')
  do j=1,4
    write(88,'(i3,6(1x,es22.14))') j,-1.d0/widths(j),-1.d0,1.d0/widths(j),0.d0,0.d0,1.d0
  end do
  close(88)
  open(89,file='umat_material_energy.csv',status='replace')
  write(89,'(a)') 'h_mm,G_N_per_mm,relative_error,final_damage'
  open(90,file='umat_material_softening.csv',status='replace')
  write(90,'(a)') 'h_mm,strain,stress_MPa'
  open(91,file='umat_orientation_energy.csv',status='replace')
  write(91,'(a)') 'base_h_mm,angle_deg,projected_width_mm,G_N_per_mm,relative_error'
  do j=1,4
    nx=1;ny=0
    el=j;h=widths(j);statev=0
    call update(eps0/4)
    if(abs(statev(1)/(eps0/4)-1.d0)>1.d-10) stop 1
    if(abs(statev(3)/h-1.d0)>1.d-10 .or. statev(4)/=1.d0) stop 2
    statev=0
    call update(-eps0/4)
    if(abs(statev(1)/((eps0/4)/props(5))-1.d0)>1.d-10) stop 3
    statev=0;last_e=0;last_s=0;G=0
    ef=eps0/2+props(4)/(h*props(3));decay=ef-eps0
    do i=1,3080
      if(i<=80) then
        e=eps0*real(i-1,8)/79.d0
      else
        e=eps0+decay/3000+real(i-81,8)*(15*decay-decay/3000)/2999.d0
      end if
      o_commit=statev(2)
      call update(e)
      if(statev(2)<o_commit) stop 4
      G=G+.5d0*(stress(1)+last_s)*(e-last_e)*h
      last_s=stress(1);last_e=e
      write(90,'(es20.12,a,es20.12,a,es20.12)') h,',',e,',',stress(1)
    end do
    write(89,'(es20.12,a,es20.12,a,es20.12,a,es20.12)') h,',',G,',',(G-props(4))/props(4),',',statev(2)
    if(abs(G/props(4)-1)>1.d-2) stop 5
    statev=0
    call update(eps0+decay)
    o_commit=statev(2);k_commit=statev(1)
    do i=1,3
      if(i==1) ratio=.25d0
      if(i==2) ratio=.8d0
      if(i==3) ratio=1.d0
      call update(ratio*(eps0+decay))
      if(abs(statev(2)-o_commit)>1.d-12.or.abs(statev(1)-k_commit)>1.d-12) stop 6
    end do
    do k=1,4
      angle=angles(k)*pi/180;nx=cos(angle);ny=sin(angle)
      h_projected=2.d0/(abs(-nx/h-ny)+abs(nx/h)+abs(ny))
      statev=0
      call update(eps0/4)
      if(abs(statev(1)/(eps0/4)-1)>1.d-10) stop 7
      if(abs(statev(3)/h_projected-1)>1.d-10) stop 8
      statev=0;last_e=0;last_s=0;G=0
      ef=eps0/2+props(4)/(h_projected*props(3));decay=ef-eps0
      do i=1,3080
        if(i<=80) then
          e=eps0*real(i-1,8)/79.d0
        else
          e=eps0+decay/3000+real(i-81,8)*(15*decay-decay/3000)/2999.d0
        end if
        call update(e)
        s_projected=stress(1)*nx*nx+stress(2)*ny*ny+2*stress(3)*nx*ny
        G=G+.5d0*(s_projected+last_s)*(e-last_e)*h_projected
        last_s=s_projected;last_e=e
      end do
      write(91,'(es20.12,4(a,es20.12))') h,',',angles(k),',',h_projected,',',G,',',(G-props(4))/props(4)
      if(abs(G/props(4)-1)>1.d-2) stop 9
    end do
  end do
  close(89);close(90);close(91)
  print *, 'UMAT mapping, width, energy, unload/reload, and rotated-strain checks passed.'
contains
  subroutine update(target)
    real(8),intent(in)::target
    dstrain=[target*(nx*nx-props(2)*ny*ny),target*(ny*ny-props(2)*nx*nx), &
      2*target*(1+props(2))*nx*ny]-strain
    call umat(stress,statev,dds,sse,spd,scd,rpl,ddsdt,drplde,drpldt, &
      strain,dstrain,t,dt,temp,dtemp,predef,dpred,cmname,2,1,3,4,props,5, &
      coords,drot,pnewdt,celent,f0,f1,el,1,1,1,jstep,1)
    strain=strain+dstrain
  end subroutine
end program
subroutine getoutdir(outdir,length)
  implicit none
  character(*)::outdir
  integer::length
  outdir='.';length=1
end subroutine
