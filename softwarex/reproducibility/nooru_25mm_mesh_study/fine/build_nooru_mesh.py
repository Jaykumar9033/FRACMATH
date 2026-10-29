# Run inside Abaqus/CAE: abaqus cae noGUI=build_nooru_mesh.py
# Mesh only; the numerical pure-tension calculation runs in MATLAB.
from abaqus import mdb
from abaqusConstants import THREE_D, DEFORMABLE_BODY, FREE, TET, C3D4, STANDARD, FINER
import mesh
import json
import os

seed = float(os.environ.get('NOORU_SEED_MM', '9'))
model = mdb.Model(name='Nooru25mm')
sketch = model.ConstrainedSketch(name='profile', sheetSize=500)
outline = [(0,-110),(200,-110),(200,-12.5),(175,-12.5),
           (175,-7.5),(200,-7.5),(200,90),(0,90),
           (0,-7.5),(25,-7.5),(25,-12.5),(0,-12.5)]
for index in range(len(outline)):
    sketch.Line(point1=outline[index], point2=outline[(index+1) % len(outline)])
part = model.Part(name='panel', dimensionality=THREE_D, type=DEFORMABLE_BODY)
part.BaseSolidExtrude(sketch=sketch, depth=50)
part.setMeshControls(regions=part.cells, elemShape=TET, technique=FREE)
part.setElementType(regions=(part.cells,), elemTypes=(mesh.ElemType(elemCode=C3D4, elemLibrary=STANDARD),))
part.seedPart(size=seed, deviationFactor=0.1, minSizeFactor=0.1)
# Refine the physical notch edges without changing the geometry.
notch_edges = []
for edge in part.edges:
    x,y,z = edge.pointOn[0]
    if abs(y+10) <= 2.500001 and (x <= 25.000001 or x >= 174.999999):
        notch_edges.append(edge)
part.seedEdgeBySize(edges=tuple(notch_edges), size=seed/3, constraint=FINER)
part.generateMesh()
with open('Job-1_nodes.txt','w') as stream:
    for node in part.nodes:
        stream.write('%d %.12g %.12g %.12g\n' % ((node.label,) + tuple(node.coordinates)))
with open('Job-1_elements.txt','w') as stream:
    for element in part.elements:
        labels = tuple(node.label for node in element.getNodes())
        stream.write('%d %d %d %d %d\n' % ((element.label,) + labels))
for name,axis,value in [('top',1,90),('bottom',1,-110),('left',0,0),('right',0,200)]:
    with open('Job-1_%s_nodes.txt' % name,'w') as stream:
        for node in part.nodes:
            if abs(node.coordinates[axis]-value) < 1e-7:
                stream.write('%d\n' % node.label)
with open('mesh_metadata.json','w') as stream:
    json.dump(dict(nodes=len(part.nodes), elements=len(part.elements), dofs=3*len(part.nodes),
                   global_seed_mm=seed, notch_seed_mm=seed/3,
                   dimensions_mm=[200,200,50], notch_depth_mm=25, notch_width_mm=5,
                   coordinate_bounds_mm=[[0,-110,0],[200,90,50]], outline=outline), stream, indent=2)
print('Nooru 25 mm notch mesh exported: %d nodes, %d TET4 elements' % (len(part.nodes),len(part.elements)))
