from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import zarr
from pymmcore_plus import CMMCorePlus
from pymmcore_plus.mda import MDAEngine
from useq import MDASequence

from pymmcore_mda_writers import zarr_MDA_writer

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_engine_registration(core: CMMCorePlus, tmp_path: Path, qtbot: "QtBot"):
    mda = MDASequence(
        stage_positions=[(1, 1, 1)],
        z_plan={"range": 3, "step": 1},
        channels=[{"config": "DAPI", "exposure": 1}],
    )

    writer = zarr_MDA_writer(  # noqa
        tmp_path / "zarr_{run}.zarr", (512, 512), dtype=np.uint16, core=core
    )
    new_engine = MDAEngine(core)
    with qtbot.waitSignal(core.events.mdaEngineRegistered):
        core.register_mda_engine(new_engine)
    with qtbot.waitSignal(core.mda.events.sequenceFinished):
        core.run_mda(mda)
    arr = np.asarray(zarr.open(tmp_path / "zarr_0.zarr"))
    assert arr.shape == (1, 1, 4, 512, 512)
    for i in range(4):
        assert not np.all(arr[0, 0, i] == 0)
