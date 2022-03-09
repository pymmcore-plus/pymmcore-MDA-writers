import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import zarr
from pymmcore_plus import CMMCorePlus
from pymmcore_plus.mda import MDAEngine
from useq import MDASequence

from pymmcore_mda_writers import BaseWriter, SimpleMultiFileTiffWriter, ZarrWriter

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


@pytest.fixture
def core() -> CMMCorePlus:
    mmc = CMMCorePlus.instance()
    if len(mmc.getLoadedDevices()) < 2:
        mmc.loadSystemConfiguration(str(Path(__file__).parent / "test-config.cfg"))
    return mmc


def test_engine_registration(core: CMMCorePlus, tmp_path: Path, qtbot: "QtBot"):
    mda = MDASequence(
        metadata={"blah": "blah blah blah"},
        stage_positions=[(1, 1, 1)],
        z_plan={"range": 3, "step": 1},
        channels=[{"config": "DAPI", "exposure": 1}],
    )

    writer = ZarrWriter(  # noqa
        tmp_path / "zarr_data", (512, 512), dtype=np.uint16, core=core
    )
    new_engine = MDAEngine(core)
    with qtbot.waitSignal(core.events.mdaEngineRegistered):
        core.register_mda_engine(new_engine)
    with qtbot.waitSignal(core.mda.events.sequenceFinished):
        core.run_mda(mda)
    with qtbot.waitSignal(core.mda.events.sequenceFinished):
        core.run_mda(mda)
    run1 = zarr.open(tmp_path / "zarr_data_1.zarr")
    arr1 = np.asarray(run1)
    run2 = zarr.open(tmp_path / "zarr_data_2.zarr")
    arr2 = np.asarray(run2)
    assert arr1.shape == (1, 1, 4, 512, 512)
    assert arr2.shape == (1, 1, 4, 512, 512)
    for i in range(4):
        assert not np.all(arr1[0, 0, i] == 0)
        assert not np.all(arr2[0, 0, i] == 0)
    attrs = run2.attrs.asdict()
    assert "tpczyx" == attrs["axis_order"]
    assert mda == MDASequence(**json.loads(attrs["useq-sequence"]))


def test_tiff_writer(core: CMMCorePlus, tmp_path: Path, qtbot: "QtBot"):
    mda = MDASequence(
        metadata={"blah": "blah blah blah"},
        time_plan={"interval": 0.1, "loops": 2},
        stage_positions=[(1, 1, 1)],
        z_plan={"range": 3, "step": 1},
        channels=[{"config": "DAPI", "exposure": 1}],
    )
    writer = SimpleMultiFileTiffWriter(str(tmp_path / "mda_data"), core=core)  # noqa

    # run twice to check that we aren't overwriting files
    with qtbot.waitSignal(core.mda.events.sequenceFinished):
        core.run_mda(mda)
    with qtbot.waitSignal(core.mda.events.sequenceFinished):
        core.run_mda(mda)

    # check that the correct folders/files were generated
    data_folders = set(tmp_path.glob("mda_data*"))
    assert {tmp_path / "mda_data_1", tmp_path / "mda_data_2"}.issubset(
        set(data_folders)
    )
    expected = [
        Path("t000_p000_c000_z000.tiff"),
        Path("t001_p000_c000_z000.tiff"),
        Path("t001_p000_c000_z002.tiff"),
        Path("t001_p000_c000_z001.tiff"),
        Path("t000_p000_c000_z001.tiff"),
        Path("t001_p000_c000_z003.tiff"),
        Path("t000_p000_c000_z002.tiff"),
        Path("t000_p000_c000_z003.tiff"),
    ]
    actual_1 = list((tmp_path / "mda_data_1").glob("*"))
    actual_2 = list((tmp_path / "mda_data_2").glob("*"))
    for e in expected:
        assert tmp_path / "mda_data_1" / e in actual_1
        assert tmp_path / "mda_data_2" / e in actual_2
    with open(tmp_path / "mda_data_1" / "useq-sequence.json") as f:
        seq = MDASequence(**json.load(f))
    assert seq == mda


def test_missing_deps():
    with patch("pymmcore_mda_writers._writers.tifffile", None):
        with pytest.raises(ValueError) as e:
            SimpleMultiFileTiffWriter("blarg")
        assert "requires tifffile to be installed" in str(e)
    with patch("pymmcore_mda_writers._writers.zarr", None):
        with pytest.raises(ValueError) as e:
            ZarrWriter("blarg", (512, 512), np.uint16)
        assert "requires zarr to be installed" in str(e)


def test_deregistration(core: CMMCorePlus, qtbot: "QtBot"):
    mda = MDASequence(
        stage_positions=[(1, 1, 1)],
        time_plan={"interval": 0.1, "loops": 3},
        channels=[{"config": "DAPI", "exposure": 1}],
    )

    writer = BaseWriter(core)
    writer._disconnect(core.mda)
    writer._onMDAFrame = MagicMock()
    writer._on_mda_engine_registered(core.mda, None)
    new_engine = MDAEngine(core)
    with qtbot.waitSignal(core.events.mdaEngineRegistered):
        core.register_mda_engine(new_engine)
    with qtbot.waitSignal(core.mda.events.sequenceFinished):
        core.run_mda(mda)
    writer.disconnect()
    with qtbot.waitSignal(core.mda.events.sequenceFinished):
        core.run_mda(mda)
    assert writer._onMDAFrame.call_count == 3
