"""Time actual UMAT calls in a separate serial Abaqus run.

The constitutive statements stay unchanged. SYSTEM_CLOCK brackets each call.
This includes clock overhead and scheduling; it is not an assembly timer.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np

from run_scaling_study import setup, env_abq
from run_mesh_study import launch, command_abaqus


def instrument(source):
    start = """C     Serial timing only; production constitutive equations unchanged.
      INTEGER*8 TSTART,TEND,TTICKS,TCALLS,TRATE,TEMPTY
      COMMON /FRAC_TIMER/ TTICKS,TCALLS,TRATE,TEMPTY
      SAVE /FRAC_TIMER/
      CALL SYSTEM_CLOCK(TSTART)

"""
    source = source.replace('C----- Material constants', start+'C----- Material constants', 1)
    source = source.replace('      RETURN\n      END', """      CALL SYSTEM_CLOCK(TEND)
      TTICKS=TTICKS+MAX(0_8,TEND-TSTART)
      TCALLS=TCALLS+1_8
      RETURN
      END""", 1)
    index = source.index('      IF (LOP', source.index('      SUBROUTINE UEXTERNALDB'))
    timing = """      INTEGER*8 TTICKS,TCALLS,TRATE,TEMPTY,TA,TB
      INTEGER ITEST
      COMMON /FRAC_TIMER/ TTICKS,TCALLS,TRATE,TEMPTY
      SAVE /FRAC_TIMER/
      IF (LOP .EQ. 0) THEN
         TTICKS=0_8
         TCALLS=0_8
         TEMPTY=0_8
         CALL SYSTEM_CLOCK(COUNT_RATE=TRATE)
         DO ITEST=1,100000
            CALL SYSTEM_CLOCK(TA)
            CALL SYSTEM_CLOCK(TB)
            TEMPTY=TEMPTY+MAX(0_8,TB-TA)
         END DO
      END IF
      IF (LOP .EQ. 3) THEN
         WRITE(6,*) 'FRAC_TIMER calls ',TCALLS
         WRITE(6,*) 'FRAC_TIMER clock_rate ',TRATE
         WRITE(6,*) 'FRAC_TIMER umat_elapsed_s ',
     &       DBLE(TTICKS)/DBLE(TRATE)
         WRITE(6,*) 'FRAC_TIMER empty_pair_mean_s ',
     &       DBLE(TEMPTY)/DBLE(TRATE)/100000.D0
      END IF
"""
    return source[:index]+timing+source[index:]


def analyze(folder, baseline):
    job = folder/'Gregoire_3PB'
    if 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' not in (job/'Gregoire_3PB.sta').read_text():
        raise ValueError('Abaqus analysis did not complete')
    response = np.loadtxt(job/'results/abaqus_load_cmod.csv', delimiter=',', comments='#')
    reference = np.loadtxt(baseline/'results/abaqus_load_cmod.csv', delimiter=',', comments='#')
    if not np.array_equal(response, reference):
        raise ValueError('Timed response differs from baseline')
    hashes = {}
    for name in ['nodes.txt','elements.txt','top_nodes.txt','left_nodes.txt',
                 'right_nodes.txt','cmod1.txt','cmod2.txt']:
        digest = hashlib.sha256((job/'matlab_mesh'/name).read_bytes()).hexdigest()
        if digest != hashlib.sha256((baseline/'matlab_mesh'/name).read_bytes()).hexdigest():
            raise ValueError('Mesh/boundary mismatch: '+name)
        hashes[name] = digest
    dat = (job/'Gregoire_3PB.dat').read_text(errors='replace')
    # At analysis shutdown this installation routes unit 6 to the job log.
    dat += '\n'+(job/'Gregoire_3PB.log').read_text(errors='replace')
    measurements = {key:float(value.replace('D','E')) for key,value in
                    re.findall(r'FRAC_TIMER\s+(\w+)\s+([\d.EeDd+-]+)',dat)}
    if set(measurements)!=set(['calls','clock_rate','umat_elapsed_s','empty_pair_mean_s']):
        raise ValueError('Missing persisted UMAT timer records')
    msg = (job/'Gregoire_3PB.msg').read_text(errors='replace')
    passes = re.findall(r'SOLVER ELAPSED TIME:\s*([\d.Ee+-]+)\s*(ms|s)\b',msg)
    def count(pattern):
        match = re.search(pattern,msg)
        if not match:
            raise ValueError('Missing completed-job diagnostic: '+pattern)
        return int(match.group(1))
    diagnostics = dict(accepted_increments=count(r'TOTAL OF\s+(\d+)\s+INCREMENTS'),
                       solver_passes=count(r'(\d+)\s+PASSES THROUGH THE EQUATION SOLVER'),
                       factorizations=count(r'(\d+)\s+INVOLVE MATRIX DECOMPOSITION'),
                       cutbacks=count(r'(\d+)\s+CUTBACKS IN AUTOMATIC INCREMENTATION'),
                       solver_elapsed_s=sum(float(v)*(.001 if u=='ms' else 1) for v,u in passes))
    diagnostics['analysis_wall_s'] = float(re.search(r'WALLCLOCK TIME\s*\(SEC\)\s*=\s*([\d.Ee+-]+)',msg).group(1))
    if len(passes)!=diagnostics['solver_passes']:
        raise ValueError('Solver timer/pass-count mismatch')
    report = dict(scope='Serial actual-UMAT elapsed-call timer; separate instrumented job.',
                  response_arrays_exactly_equal=True, response_rows=len(response),
                  mesh_sha256=hashes, measurements=measurements,
                  diagnostics=diagnostics,
                  empty_clock_pair_projection_s=measurements['calls']*measurements['empty_pair_mean_s'],
                  limitations=['Elapsed-call sum includes clock overhead and possible scheduling.',
                               'Empty-pair projection is a diagnostic, not a subtraction or exact overhead correction.',
                               'Measures UMAT calls only; excludes other Abaqus material routines and assembly.',
                               'Single CPU only; shared counters are not valid for SMP.'])
    (folder/'direct_timing_summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--source-snapshot',type=Path,required=True)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--analyze-only',action='store_true')
    args = parser.parse_args()
    folder = args.workspace.resolve()
    if not args.analyze_only:
        if folder.exists():
            raise ValueError('Use a new workspace for each timed run')
        setup(folder,args.source_snapshot.resolve())
        umat = folder/'cdm_umat_2d_OLIVER_T3_FAST.for'
        umat.write_text(instrument(umat.read_text()))
        launch(command_abaqus(folder),folder,env_abq('small','coarse',2000,-.1,cpus=1),folder/'run.log')
    analyze(folder,args.baseline.resolve())


if __name__ == '__main__':
    main()
