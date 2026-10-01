"""Extract completed mesh-study ODBs without submitting an analysis."""
import argparse,os,shutil,time
from pathlib import Path
from run_mesh_study import ABAQUS_SOURCE,command_abaqus,launch

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace',type=Path,required=True)
    parser.add_argument('--meshes',nargs='+',choices=['coarse','medium','fine'],default=['coarse','medium','fine'])
    parser.add_argument('--wait',action='store_true')
    args=parser.parse_args()
    for name in args.meshes:
        case=args.workspace.resolve()/name
        result=case/'Gregoire_3PB/results/abaqus_load_cmod.csv'
        while not (case/'abaqus.sampling.json').exists():
            if not args.wait:raise RuntimeError('Analysis process has not finished: '+name)
            time.sleep(10)
        sta=case/'Gregoire_3PB/Gregoire_3PB.sta'
        if not sta.exists() or 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' not in sta.read_text(errors='replace'):
            raise RuntimeError('Analysis did not complete successfully: '+name)
        if result.exists():
            print('Response already exported: '+name,flush=True)
            continue
        shutil.copy2(ABAQUS_SOURCE/'run_3pb_abaqus_OLIVER_T3_FAST.py',case/'run_3pb_abaqus_OLIVER_T3_FAST.py')
        env=os.environ.copy();env.update(ABQ_EXTRACT_ONLY='1',ABQ_AUTO_PLOT='0')
        launch(command_abaqus(case),case,env,case/'extract.log')
        if not result.exists():raise RuntimeError('ODB extraction failed; inspect abaqus.rpy: '+name)
        print('Exported completed ODB: '+name,flush=True)

if __name__=='__main__':main()
