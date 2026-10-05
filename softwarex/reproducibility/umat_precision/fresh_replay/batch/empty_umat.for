C=======================================================================
C  CDM_UMAT_2D_OLIVER_T3_FAST.FOR
C
C  Faster Abaqus/Standard UMAT for CPS3 plane-stress scalar CDM.
C  Uses MATLAB-equivalent Oliver direction-dependent T3 crack-band width:
C
C       h(n) = 2 / SUM_a | grad(N_a) dot n |,  a = 1..3
C
C  Required job-folder file:
C       oliver_t3_gradN.dat
C  Format:
C       NOEL, g1x, g1y, g2x, g2y, g3x, g3y
C
C  Speed notes:
C    - UMAT is still called point-by-point by Abaqus/Standard; true
C      block vectorization is not possible inside a Standard UMAT.
C    - This file removes small matrix loops in the stress/tangent update.
C    - Use *DEPVAR, n=2 for fastest output: STATEV(1)=kappa, STATEV(2)=omega.
C      If n>=4, STATEV(3)=h and STATEV(4)=Oliver flag are stored for checking.
C=======================================================================
      SUBROUTINE EMPTY_UMAT(STRESS, STATEV, DDSDDE, SSE, SPD, SCD,
     1  RPL, DDSDDT, DRPLDE, DRPLDT,
     2  STRAN, DSTRAN, TIME, DTIME, TEMP, DTEMP, PREDEF, DPRED,
     3  CMNAME, NDI, NSHR, NTENS, NSTATV, PROPS, NPROPS, COORDS,
     4  DROT, PNEWDT, CELENT, DFGRD0, DFGRD1, NOEL, NPT, LAYER,
     5  KSPT, JSTEP, KINC)

      INCLUDE 'ABA_PARAM.INC'

      CHARACTER*80 CMNAME
      REAL*8 SSE, SPD, SCD, RPL, DRPLDT, DTIME, TEMP, DTEMP
      REAL*8 PNEWDT, CELENT
      DIMENSION STRESS(NTENS), STATEV(NSTATV), DDSDDE(NTENS,NTENS),
     1  DDSDDT(NTENS), DRPLDE(NTENS), STRAN(NTENS), DSTRAN(NTENS),
     2  TIME(2), PREDEF(1), DPRED(1), PROPS(NPROPS), COORDS(3),
     3  DROT(3,3), DFGRD0(3,3), DFGRD1(3,3), JSTEP(4)

      REAL*8 E, ANU, FT, GF, FCFT, EPS0
      REAL*8 KAPPA, OMEGA, OMEGA_NEW, FAC
      REAL*8 EXX, EYY, GXY, EM, RAD, E1, E2, E3
      REAL*8 I1, J2, A1, A2, A3, A4, INSIDE, EQ
      REAL*8 EF, H, C11, C12, C33, DENOM
      INTEGER I, J, IHFLAG
      REAL*8 OMAX
      PARAMETER (OMAX = 0.999999999999D0)

      RETURN
      END
