# -*- coding: mbcs -*-
#
# Abaqus/CAE Release 2024 replay file
# Internal Version: 2023_09_21-06.55.25 RELr426 190762
# Run by jmavani on Sat Oct  3 23:06:33 2026
#

# from driverUtils import executeOnCaeGraphicsStartup
# executeOnCaeGraphicsStartup()
#: Executing "onCaeGraphicsStartup()" in the site directory ...
from abaqus import *
from abaqusConstants import *
session.Viewport(name='Viewport: 1', origin=(1.11979, 1.1169), width=164.833, 
    height=110.796)
session.viewports['Viewport: 1'].makeCurrent()
from driverUtils import executeOnCaeStartup
executeOnCaeStartup()
execfile('build_nooru_mesh.py', __main__.__dict__)
#: The model "Nooru25mm" has been created.
#: Nooru 25 mm notch mesh exported: 28258 nodes, 144791 TET4 elements
print('RT script done')
#: RT script done
