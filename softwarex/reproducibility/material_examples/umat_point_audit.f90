! Read material-point cases and call the repository UMAT without changing it.
! Abaqus provides GETOUTDIR and XIT in an actual analysis.
program point_audit
  implicit none
  integer :: case_id, element, status, step(4), i
  real(8) :: stress(3), state(4), tangent(3,3), strain(3), increment(3)
  real(8) :: props(5), time(2), coordinates(3), rotation(3,3), f0(3,3), f1(3,3)
  real(8) :: sse, spd, scd, rpl, ddsdt(3), drplde(3), drpldt, pnewdt
  real(8) :: predef(1), dpred(1)
  character(80) :: name
  props=[37000.d0,.2d0,3.5d0,.09d0,10.d0]
  time=0; coordinates=0; rotation=0; f0=0; f1=0
  predef=0; dpred=0; step=[1,1,0,0]; name='CONCRETE'
  call uexternaldb(0,0,time,.001d0,1,0)
  open(10,file='point_inputs.csv',status='old')
  open(11,file='point_outputs.csv',status='replace')
  do
    read(10,*,iostat=status) case_id,element,strain,increment,state(1:2)
    if(status/=0) exit
    stress=0; state(3:4)=0; tangent=0
    sse=0; spd=0; scd=0; rpl=0; ddsdt=0; drplde=0; drpldt=0; pnewdt=1
    call umat(stress,state,tangent,sse,spd,scd,rpl,ddsdt,drplde,drpldt, &
      strain,increment,time,.001d0,0.d0,0.d0,predef,dpred,name,2,1,3,4, &
      props,5,coordinates,rotation,pnewdt,99.d0,f0,f1,element,1,1,1,step,1)
    write(11,'(i6,16(a,es24.16))') case_id, &
      (',',stress(i),i=1,3),(',',state(i),i=1,4), &
      (',',tangent(i,1),i=1,3),(',',tangent(i,2),i=1,3), &
      (',',tangent(i,3),i=1,3)
  end do
  close(10); close(11)
end program

subroutine getoutdir(folder,length)
  implicit none
  character(*) :: folder
  integer :: length
  folder='.'; length=1
end subroutine

subroutine xit
  implicit none
  error stop 'Missing gradient table entry in material-point audit'
end subroutine
