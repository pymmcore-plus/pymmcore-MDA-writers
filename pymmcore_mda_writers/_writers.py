__all__ = [
    "zarr_MDA_writer",
]
from typing import Optional

import numpy as np
import zarr
from pymmcore_plus import CMMCorePlus
from pymmcore_plus.mda import PMDAEngine
from useq import MDAEvent, MDASequence


class zarr_MDA_writer:
    def __init__(self, store_name, img_shape, dtype, core: CMMCorePlus = None):
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
        self._core = core or CMMCorePlus.instance()
        self._store_name = str(store_name)
        self._run_number = -1
        self._img_shape = img_shape
        self._dtype = dtype
        self._on_mda_engine_registered(core.mda, None)
        self._core.events.mdaEngineRegistered.connect(self._on_mda_engine_registered)
        # TODO: add canceled, finished and maybe paused?

    def _on_mda_engine_registered(
        self, newEngine: PMDAEngine, oldEngine: Optional[PMDAEngine] = None
    ):
        if oldEngine:
            self._disconnect(oldEngine)
        newEngine.events.sequenceStarted.connect(self._onMDAStarted)
        newEngine.events.frameReady.connect(self._onMDAFrame)

    def _disconnect(self, engine):
        engine.events.sequenceStarted.disconnect(self._onMDAStarted)
        engine.events.frameReady.disconnect(self._onMDAFrame)

    def disconnect(self):
        "Disconnect this writer from processing any more events"
        self._disconnect(self._core.mda)

    def _onMDAStarted(self, sequence: MDASequence):
        self._current_sequence = sequence

        # hacky way to drop unncessary parts of the axis order
        # e.g. drop the `p` in `tpcz` if there is only one position
        # TODO: think about making this better/more robust
        event = next(sequence.iter_events())
        event_axes = list(event.index.keys())
        self._axis_order = tuple(a for a in sequence.axis_order if a in event_axes)

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
