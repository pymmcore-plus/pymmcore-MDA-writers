"""
ZarrWriter

This writer will write a single zarr file.
That file can then be opened with zarr.open
"""

import json

import numpy as np
import zarr
from pymmcore_plus import CMMCorePlus
from useq import MDASequence

from pymmcore_mda_writers import ZarrWriter

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

# the zarr writer requires that give it the dtype and shape of images on init
# For the demo camera these will be (512, 512) and uint16 respectively
writer = ZarrWriter("data/zarr_writer_example/run", (512, 512), np.uint16)


# run the MDA twice
# the writer will not overwrite an existing store
# instead it will make a new one automatically

th = core.run_mda(mda)
th.join()

th = core.run_mda(mda)
th.join()

# If you run  may need to increment
run_1 = zarr.open("data/zarr_writer_example/run_1.zarr")
run_2 = zarr.open("data/zarr_writer_example/run_2.zarr")


print(run_2)

# metadata as well as the original MDASequence are stored
# in the zarr `.attrs`

print(run_2.attrs.asdict())

# you can fully reconstruct the original sequence like so
saved_sequence_as_useq = MDASequence(**json.loads(run_2.attrs["useq-sequence"]))
print(saved_sequence_as_useq)
