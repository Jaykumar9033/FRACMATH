@echo off
call "C:\Program Files (x86)\Intel\oneAPI\compiler\2025.0\env\vars.bat" intel64 vs2022
if errorlevel 1 exit /b 1
ifx /O2 /extend-source /names:lowercase /include:"C:\SIMULIA\EstProducts\2024\SMAUsubs\PublicInterfaces" cdm_umat_2d_OLIVER_T3_FAST.for empty_umat.for kernel32.lib benchmark_umat_batches.f90 /exe:benchmark_umat_batches.exe
if errorlevel 1 exit /b 1
benchmark_umat_batches.exe
