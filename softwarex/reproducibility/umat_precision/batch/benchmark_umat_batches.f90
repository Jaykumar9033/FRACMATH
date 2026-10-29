! Time many calls with clocks outside the loops. Production UMAT is unchanged.
! This is a standalone material-point benchmark, not an Abaqus job timer.
program benchmark_batches
  use iso_c_binding, only: c_int, c_int64_t
  implicit none
  interface
    function qpc(value) bind(C,name='QueryPerformanceCounter') result(ok)
      import c_int,c_int64_t
      integer(c_int64_t),intent(out) :: value
      integer(c_int) :: ok
    end function
    function qpf(value) bind(C,name='QueryPerformanceFrequency') result(ok)
      import c_int,c_int64_t
      integer(c_int64_t),intent(out) :: value
      integer(c_int) :: ok
    end function
  end interface
  integer, parameter :: n=712, cycles=20000, repeats=5
  real(8) :: inputs(10,n), stress(3), state(4), tangent(3,3)
  real(8) :: strain(3), increment(3), props(5), time(2), coordinates(3)
  real(8) :: rotation(3,3), f0(3,3), f1(3,3), predef(1), dpred(1)
  real(8) :: sse,spd,scd,rpl,ddsdt(3),drplde(3),drpldt,pnewdt
  real(8) :: checksum, cpu_start,cpu_end
  integer :: i,j,k,mode,repeat,element,step(4),ok
  integer(8) :: first,last,rate,empty_ticks,a,b,min_tick
  character(80) :: name
  open(10,file='point_inputs.csv',status='old')
  do i=1,n
    read(10,*) inputs(:,i)
  end do
  close(10)
  props=[37000.d0,.2d0,3.5d0,.09d0,10.d0]
  time=0;coordinates=0;rotation=0;f0=0;f1=0;predef=0;dpred=0
  step=[1,1,0,0];name='CONCRETE'
  call uexternaldb(0,0,time,.001d0,1,0)
  ! One untimed pass loads instructions and checks initialization.
  do i=1,n
    call run_case(i,1)
  end do
  open(11,file='batch_timings.csv',status='replace')
  write(11,'(a)') 'repeat,mode,calls,elapsed_s,cpu_s,checksum'
  ok=qpf(rate)
  if(ok==0.or.rate<=0) error stop 'High-resolution frequency unavailable'
  empty_ticks=0;min_tick=huge(min_tick)
  do i=1,100000
    ok=qpc(a)
    if(ok==0) error stop 'Counter unavailable'
    ok=qpc(b)
    if(ok==0.or.b<a) error stop 'Invalid clock calibration'
    empty_ticks=empty_ticks+b-a
    if(b>a) min_tick=min(min_tick,b-a)
  end do
  open(12,file='clock_calibration.csv',status='replace')
  write(12,'(a)') 'rate_hz,pairs,mean_pair_s,min_positive_delta_s'
  write(12,'(i14,a,i8,2(a,es24.16))') rate,',',100000,',', &
    real(empty_ticks,8)/rate/100000,',',real(min_tick,8)/rate
  close(12)
  do repeat=1,repeats
    ! Alternate the order to reduce a systematic warm-up/order effect.
    do k=1,2
      mode=k
      if(mod(repeat,2)==0) mode=3-k
      checksum=0
      call cpu_time(cpu_start)
      ok=qpc(first)
      if(ok==0) error stop 'Counter unavailable'
      do j=1,cycles
        do i=1,n
          call run_case(i,mode)
          checksum=checksum+sum(stress)+sum(state)+sum(tangent)
        end do
      end do
      ok=qpc(last)
      if(ok==0.or.last<first) error stop 'Invalid timing interval'
      call cpu_time(cpu_end)
      write(11,'(i3,a,i1,a,i12,3(a,es24.16))') repeat,',',mode,',', &
        int(n,8)*cycles,',',real(last-first,8)/real(rate,8),',', &
        cpu_end-cpu_start,',',checksum
      flush(11)
    end do
  end do
  close(11)
  write(*,*) 'Clock rate: ',rate
contains
  subroutine run_case(i,mode)
    integer,intent(in) :: i,mode
    element=int(inputs(2,i));strain=inputs(3:5,i);increment=inputs(6:8,i)
    state(1:2)=inputs(9:10,i);state(3:4)=0;stress=0;tangent=0
    sse=0;spd=0;scd=0;rpl=0;ddsdt=0;drplde=0;drpldt=0;pnewdt=1
    if(mode==1) then
      call umat(stress,state,tangent,sse,spd,scd,rpl,ddsdt,drplde,drpldt, &
        strain,increment,time,.001d0,0.d0,0.d0,predef,dpred,name,2,1,3,4, &
        props,5,coordinates,rotation,pnewdt,99.d0,f0,f1,element,1,1,1,step,1)
    else
      call empty_umat(stress,state,tangent,sse,spd,scd,rpl,ddsdt,drplde,drpldt, &
        strain,increment,time,.001d0,0.d0,0.d0,predef,dpred,name,2,1,3,4, &
        props,5,coordinates,rotation,pnewdt,99.d0,f0,f1,element,1,1,1,step,1)
    end if
  end subroutine
end program

subroutine getoutdir(folder,length)
  implicit none
  character(*) :: folder
  integer :: length
  folder='.';length=1
end subroutine
subroutine xit
  implicit none
  error stop 'Missing gradient table entry'
end subroutine
