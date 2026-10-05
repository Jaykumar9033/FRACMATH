@echo off
call "C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\env\vars.bat" intel64 vs2022
if errorlevel 1 exit /b 1
ifx /O2 /extend-source /names:lowercase /include:"C:\SIMULIA\EstProducts\2024\SMAUsubs\PublicInterfaces" cdm_umat_2d_OLIVER_T3_FAST.for  umat_point_audit.f90 /exe:umat_point_audit.exe
if errorlevel 1 exit /b 1
umat_point_audit.exe
