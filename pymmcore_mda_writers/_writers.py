__all__ = [
    "BaseWriter",
    "ZarrMDAWriter",
]
from pathlib import Path
from typing import Optional, Tuple, Union

import numpy as np
import numpy.typing as npt
import zarr
from pymmcore_plus import CMMCorePlus
from pymmcore_plus.mda import PMDAEngine
from useq import MDAEvent, MDASequence


class BaseWriter:
    def __init__(self, core: CMMCorePlus = None) -> None:
        self._core = core or CMMCorePlus.instance()
        self._on_mda_engine_registered(self._core.mda, None)
        self._core.events.mdaEngineRegistered.connect(self._on_mda_engine_registered)
        # TODO add paused and finished events

    def _onMDAStarted(self, sequence: MDASequence):
        ...

    def _onMDAFrame(self, img: np.ndarray, event: MDAEvent):
        ...

    def _on_mda_engine_registered(
        self, newEngine: PMDAEngine, oldEngine: Optional[PMDAEngine] = None
    ):
        if oldEngine:
            self._disconnect(oldEngine)
        newEngine.events.sequenceStarted.connect(self._onMDAStarted)
        newEngine.events.frameReady.connect(self._onMDAFrame)

    def _disconnect(self, engine: PMDAEngine):
        engine.events.sequenceStarted.disconnect(self._onMDAStarted)
        engine.events.frameReady.disconnect(self._onMDAFrame)

    def disconnect(self):
        "Disconnect this writer from processing any more events"
        self._disconnect(self._core.mda)

    @staticmethod
    def get_unique_folder(folder_base_name: Union[str, Path]) -> Path:
        """Get a unique foldername of the form '{folder_base_name}_{i}'"""
        base_path = Path.cwd()
        folder = str(folder_base_name)
        path: Path = base_path / folder
        i = 1
        while path.exists():
            path = base_path / (folder + f"_{i}")
            i += 1
        return path

    @staticmethod
    def sequence_axis_order(seq: MDASequence) -> Tuple[str]:
        """Get the axis order using only axes that are present in events."""
        # hacky way to drop unncessary parts of the axis order
        # e.g. drop the `p` in `tpcz` if there is only one position
        # TODO: add a better implementation upstream in useq
        event = next(seq.iter_events())
        event_axes = list(event.index.keys())
        return tuple(a for a in seq.axis_order if a in event_axes)


class ZarrMDAWriter(BaseWriter):
    def __init__(
        self,
        store_name: Union[str, Path],
        img_shape: Tuple[int, int],
        dtype: npt.DTypeLike,
        core: CMMCorePlus = None,
    ):
        """
        Parameters
        ----------
        store_name : str
            Should accept .format(run=INT)
        img_shape : (int, int)
        dtype : numpy dtype
        core : CMMCorePlus, optional
            If not given the current core instance will be used.
        """
        super().__init__(core)
        self._store_name = str(store_name)
        self._run_number = -1
        self._img_shape = img_shape
        self._dtype = dtype

    def _onMDAStarted(self, sequence: MDASequence):
        self._axis_order = self.sequence_axis_order(sequence)

        self._run_number += 1
        self._z = zarr.open(
            self._store_name.format(run=self._run_number),
            mode="w",
            shape=sequence.shape + self._img_shape,
            dtype=self._dtype,
        )
        self._z.attrs["axis_order"] = sequence.axis_order + "yx"

    def _onMDAFrame(self, img: np.ndarray, event: MDAEvent):
        self._z[tuple(event.index[a] for a in self._axis_order)] = img
