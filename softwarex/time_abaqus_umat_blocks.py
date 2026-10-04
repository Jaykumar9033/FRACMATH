"""Measure raw elapsed time for seven UMAT blocks in a serial diagnostic job.

Block clocks are intrusive and include clock effects. No overhead subtraction
or comparison to uninstrumented phase percentages is made.
"""
import argparse
import json
import re
from pathlib import Path
from time_abaqus_umat import analyze
from run_scaling_study import setup, env_abq
from run_mesh_study import launch, command_abaqus

BLOCKS = ['constants_state', 'strain_history', 'projected_width',
          'damage', 'stress', 'secant_matrix', 'state_store']
MARKERS = ['C----- Material constants', 'C----- Total strain',
           'C----- Oliver bandwidth', 'C----- Exponential softening',
           'C----- Unrolled plane-stress', '      DO I = 1, NTENS',
           'C----- Store state', '      RETURN\n      END']


def instrument(source):
    original = source
    inserted = []
    declarations = """C     Diagnostic clocks: serial only, no constitutive changes.
      INTEGER*8 TSTART,TEND,TTICKS,TCALLS,TRATE,TEMPTY
      INTEGER*8 BTICKS(7),BMARK,BEND,BTEST(7),BA,BB
      INTEGER BI,ITEST
      COMMON /FRAC_TIMER/ TTICKS,TCALLS,TRATE,TEMPTY
      COMMON /FRAC_BLOCK/ BTICKS,BTEST
      SAVE /FRAC_TIMER/,/FRAC_BLOCK/
      CALL SYSTEM_CLOCK(TSTART)
      CALL SYSTEM_CLOCK(BMARK)
"""
    inserted.append(declarations)
    source = source.replace(MARKERS[0], declarations+MARKERS[0], 1)
    for index, marker in enumerate(MARKERS[1:], 1):
        clock = ('      CALL SYSTEM_CLOCK(BEND)\n'
                 f'      BTICKS({index})=BTICKS({index})+\n'
                 '     &                  MAX(0_8,BEND-BMARK)\n')
        if index < 7:
            clock += '      CALL SYSTEM_CLOCK(BMARK)\n'
        else:
            clock += ('      CALL SYSTEM_CLOCK(TEND)\n'
                      '      TTICKS=TTICKS+MAX(0_8,TEND-TSTART)\n'
                      '      TCALLS=TCALLS+1_8\n')
        assert source.count(marker) >= 1, marker
        inserted.append(clock)
        source = source.replace(marker, clock+marker, 1)
    index = source.index('      IF (LOP', source.index('      SUBROUTINE UEXTERNALDB'))
    external = """      INTEGER*8 TTICKS,TCALLS,TRATE,TEMPTY,TA,TB
      INTEGER*8 BTICKS(7),BTEST(7)
      INTEGER ITEST,BI
      COMMON /FRAC_TIMER/ TTICKS,TCALLS,TRATE,TEMPTY
      COMMON /FRAC_BLOCK/ BTICKS,BTEST
      SAVE /FRAC_TIMER/,/FRAC_BLOCK/
      IF (LOP .EQ. 0) THEN
         TTICKS=0_8
         TCALLS=0_8
         TEMPTY=0_8
         DO BI=1,7
            BTICKS(BI)=0_8
            BTEST(BI)=0_8
         END DO
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
         DO BI=1,7
            WRITE(6,*) 'FRAC_BLOCK ',BI,
     &         DBLE(BTICKS(BI))/DBLE(TRATE)
         END DO
      END IF
"""
    source = source[:index]+external+source[index:]
    restored = source.replace(external, "", 1)
    for addition in inserted:
        restored = restored.replace(addition, "", 1)
    if restored != original:
        raise ValueError("Instrumentation changed original statements")
    return source


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--source-snapshot',type=Path,required=True)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--analyze-only',action='store_true')
    args=parser.parse_args(); folder=args.workspace.resolve()
    if not args.analyze_only:
        if folder.exists(): raise ValueError('Use a new workspace')
        setup(folder,args.source_snapshot.resolve())
        umat=folder/'cdm_umat_2d_OLIVER_T3_FAST.for'
        source=umat.read_text();(folder/'uninstrumented_umat.for').write_text(source)
        umat.write_text(instrument(source))
        launch(command_abaqus(folder),folder,
               env_abq('small','coarse',2000,-.1,cpus=1),folder/'run.log')
    analyze(folder,args.baseline.resolve())
    original=(folder/'uninstrumented_umat.for').read_text()
    if instrument(original)!=(folder/'cdm_umat_2d_OLIVER_T3_FAST.for').read_text():
        raise ValueError('Archived instrumentation does not match the generator')
    report=json.loads((folder/'direct_timing_summary.json').read_text())
    report['constitutive_statements_round_trip_unchanged']=True
    text=(folder/'Gregoire_3PB/Gregoire_3PB.log').read_text(errors='replace')
    values=re.findall(r'FRAC_BLOCK\s+(\d+)\s+([\d.EeDd+-]+)',text)
    if len(values)!=7: raise ValueError('Missing block output')
    rows=[dict(block=BLOCKS[int(i)-1],raw_elapsed_s=float(v.replace('D','E')))
          for i,v in values]
    report['blocks']=rows
    report['block_sum_raw_elapsed_s']=sum(r['raw_elapsed_s'] for r in rows)
    report['seven_empty_pair_projection_s']=7*report['empty_clock_pair_projection_s']
    report['limitations'] += ['Block timers perturb execution and include clock effects.',
        'Block sums exclude between-block counter updates; total UMAT includes them.',
        'Do not use block values as uninstrumented percentages or complete Abaqus phase times.']
    (folder/'block_timing_summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__': main()
