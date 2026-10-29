"""Re-extract completed ODB histories and damage frames without rerunning Abaqus."""
import os
import run_3pb_abaqus_OLIVER_T3_FAST as workflow

workflow.extract_and_plot(
    os.path.abspath(os.path.join('Gregoire_3PB', 'Gregoire_3PB.odb')),
    849.35,
)
