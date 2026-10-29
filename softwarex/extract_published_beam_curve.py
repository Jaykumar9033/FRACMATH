"""Recover the published experiments-100-mm graphic trace from the author bundle.

Requires pypdf and NumPy. Download https://arxiv.org/src/1107.2311v2 separately.
python softwarex/extract_published_beam_curve.py --bundle C:/sources/1107.2311v2.tar.gz --output C:/runs/beam_digitization
These vertices are digitized graphic data, not original laboratory samples.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

import numpy as np
from pypdf import PdfReader

REFERENCE=Path(__file__).resolve().parent/'reproducibility/experimental_2d'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    output=args.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError('Use an empty output folder; existing evidence is preserved')
    provenance=json.loads((REFERENCE/'provenance.json').read_text(encoding='utf-8'))
    bundle=args.bundle.read_bytes()
    if hashlib.sha256(bundle).hexdigest()!=provenance['source_bundle_sha256']:
        raise ValueError('Source bundle differs from the recorded author version')
    with tarfile.open(fileobj=io.BytesIO(bundle)) as archive:
        native=archive.extractfile(provenance['figure_file']).read()
    if hashlib.sha256(native).hexdigest()!=provenance['figure_file_sha256']:
        raise ValueError('Published native figure differs from the recorded source')
    stream=PdfReader(io.BytesIO(native)).pages[0].get_contents().get_data().decode('latin-1')
    start=stream.index('(experiments 100 mm)Tj')
    block=stream[start:stream.index('(model 200 mm)Tj',start)]
    paths=[];current=None
    for line in block.splitlines():
        match=re.fullmatch(r'([\d.]+) ([\d.]+) ([ml])',line)
        if not match:
            continue
        point=(float(match[1]),float(match[2]))
        if match[3]=='m':
            current=[point];paths.append(current)
        else:
            if current is None:
                raise ValueError('Invalid source path')
            current.append(point)
    if paths.pop(0)!=[(3058.5,2018.5),(3330.0,2018.5)]:
        raise ValueError('Experimental legend sample was not identified')
    if not all(paths[i][-1]==paths[i+1][0] for i in range(len(paths)-1)):
        raise ValueError('Experimental trace is not continuous')
    graphic=np.array([point for i,path in enumerate(paths) for point in (path if i==0 else path[1:])])
    calibration=provenance['axis_calibration']
    x=(graphic[:,0]-calibration['x0'])*0.5/(calibration['x1']-calibration['x0'])
    y=(graphic[:,1]-calibration['y0'])*14/(calibration['y1']-calibration['y0'])
    if not np.isfinite(graphic).all() or len(graphic)!=provenance['graphic_vertex_count'] or np.any(np.diff(x)<0):
        raise ValueError('Published graphic vertices failed validation')
    output.mkdir(parents=True,exist_ok=True)
    destination=output/'published_experimental_100mm_vertices.csv'
    with destination.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.writer(stream)
        writer.writerow(['graphic_vertex_index','CMOD_mm','load_kN','graphic_x','graphic_y'])
        for i,(gx,gy) in enumerate(graphic):
            writer.writerow([i,format(x[i],'.12g'),format(y[i],'.12g'),gx,gy])
    checked=hashlib.sha256(destination.read_bytes()).hexdigest()==provenance['data_file_sha256']
    report={'passed':checked,'vertices':len(graphic),'peak_load_kN':float(y.max()),
            'peak_CMOD_mm':float(x[np.argmax(y)]),
            'scope':'Recovered published experimental graphic trace; not raw measurement samples.'}
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    if not checked:
        raise ValueError('Digitization differs from the archived graphic vertices')


if __name__=='__main__':
    main()
