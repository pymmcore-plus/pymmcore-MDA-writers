"""
TiffWriter

This writer will write individual TIFF files
with names of the form t000_p000_c000_z000.tiff
"""

from pymmcore_plus import CMMCorePlus
from useq import MDASequence

from pymmcore_mda_writers import SimpleMultiFileTiffWriter

core = CMMCorePlus.instance()
core.loadSystemConfiguration()

mda = MDASequence(
    time_plan={"interval": 0.1, "loops": 2},
    stage_positions=[(1, 1, 1)],
    z_plan={"range": 3, "step": 1},
    channels=[{"config": "DAPI", "exposure": 1}],
)

# This will automatically get the same core instance we used above
# if you are not using the core singleton make sure to pass core to
# the writer init.
writer = SimpleMultiFileTiffWriter("data/tiff_writer_example/run")


th = core.run_mda(mda)

# wait until the MDA finishes
th.join()
