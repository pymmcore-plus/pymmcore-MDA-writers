__all__ = [
    "zarr_MDA_writer",
]
import numpy as np
import zarr
from useq import MDAEvent, MDASequence


class zarr_MDA_writer:
    def __init__(self, core, store_name, img_shape=(512, 512), dtype=np.uint8):
        """
        Parameters
        ----------
        core : MMCorePlus
        store_name : str
            Should accept .format(run=INT)
        img_shape : (int, int)
        dtype : numpy dtype
        """
        self._core = core
        self._store_name = store_name
        self._run_number = -1
        self._img_shape = img_shape
        self._dtype = dtype
        self._core.events.sequenceStarted.connect(self._onMDAStarted)
        self._core.events.frameReady.connect(self._onMDAFrame)
        # TODO: add canceled, finished and maybe paused?

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

    def disconnect(self):
        "Disconnect this writer from processing any more events"
        self._core.events.onFrame.disconnect(self._onMDAFrame)
        self._core.events.frameReady.disconnect(self._onMDAStarted)
