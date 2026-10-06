import json
from pathlib import Path
import re
import sys
from odbAccess import openOdb

odb_path, metadata_path, output_path = sys.argv[1:4]
metadata = json.loads(Path(metadata_path).read_text())
odb = openOdb(odb_path, readOnly=True)
try:
    step = odb.steps['Loading']
    def history(set_name, component, average):
        labels = {int(row[0]) for row in metadata['boundary_nodes'][set_name]}
        rows = []
        for name, region in step.historyRegions.items():
            integers = re.findall(r'\d+', name)
            if not integers or int(integers[-1]) not in labels:
                continue
            if component in region.historyOutputs:
                rows.append(dict(region.historyOutputs[component].data))
        if len(rows) != len(labels):
            raise ValueError('Missing node histories: %s %s' % (set_name, component))
        times = set(rows[0])
        for row in rows[1:]:
            if set(row) != times:
                raise ValueError('Node histories have different schedules')
        return {float(t): sum(float(row[t]) for row in rows) / (len(rows) if average else 1)
                for t in times}
    force = history('Load_Nodes', 'RF2', False)
    displacement = history('Load_Nodes', 'U2', True)
    left = history('CMOD1', 'U1', True)
    right = history('CMOD2', 'U1', True)
    if not set(force) == set(displacement) == set(left) == set(right):
        raise ValueError('Load and CMOD histories have different schedules')
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w') as stream:
        stream.write('normalized_time,displacement_mm,cmod_mm,load_N\n')
        for t in sorted(force):
            stream.write('%.17g,%.17g,%.17g,%.17g\n' %
                         (t, displacement[t], abs(right[t]-left[t]), -force[t]))
    with (output.parent / 'abaqus_load_cmod.csv').open('w') as stream:
        stream.write('# cmod[mm], load[N]\n')
        for t in sorted(force):
            stream.write('%.17g,%.17g\n' % (abs(right[t]-left[t]), -force[t]))
finally:
    odb.close()
