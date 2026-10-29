"""Run ten explained material examples with the unchanged MATLAB and UMAT functions."""
import argparse
import shutil
import subprocess
from pathlib import Path
from audit_umat import prepare, check
from run_umat_precision import command_file


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--check', action='store_true')
    args=parser.parse_args()
    folder=args.workspace.resolve()
    if args.check:
        check(folder)
        return
    if folder.exists():
        raise ValueError('Use a fresh output folder to preserve previous examples.')
    package=Path(__file__).resolve().parent
    prepare(folder)
    shutil.copy2(package/'umat_point_audit.f90',folder/'umat_point_audit.f90')
    shutil.copy2(package/'reproducibility/abaqus/cdm_umat_2d_OLIVER_T3_FAST.for',folder/'cdm_umat_2d_OLIVER_T3_FAST.for')
    command_file(folder,'umat_point_audit.f90','umat_point_audit.exe')
    with (folder/'compile.log').open('w') as stream:
        subprocess.run(['cmd.exe','/d','/c','compile_run.cmd'],cwd=folder,stdout=stream,stderr=subprocess.STDOUT,check=True)
    with (folder/'matlab.log').open('w') as stream:
        subprocess.run([r'C:\Program Files\MATLAB\R2024b\bin\matlab.exe','-batch','run_matlab_points'],cwd=folder,stdout=stream,stderr=subprocess.STDOUT,check=True)
    check(folder)


if __name__=='__main__':
    main()
