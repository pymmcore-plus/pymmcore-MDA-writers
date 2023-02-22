__all__ = [
    "BaseWriter",
    "SimpleMultiFileTiffWriter",
    "ZarrWriter",
]
from pathlib import Path
from typing import Sequence, Tuple, Union

import numpy as np
import numpy.typing as npt
from pymmcore_plus import CMMCorePlus
from pymmcore_plus.mda import PMDAEngine
from useq import MDAEvent, MDASequence

try:
    import tifffile
except ModuleNotFoundError:
    tifffile = None
try:
    import zarr
except ModuleNotFoundError:
    zarr = None


class BaseWriter:
    def __init__(self, core: CMMCorePlus = None) -> None:
        self._core = core or CMMCorePlus.instance()
        self._core.mda.events.sequenceStarted.connect(self._onMDAStarted)
        self._core.mda.events.frameReady.connect(self._onMDAFrame)
        # TODO add paused and finished events

    def _onMDAStarted(self, sequence: MDASequence):
        ...

    def _onMDAFrame(self, img: np.ndarray, event: MDAEvent):
        ...  # pragma: no cover

    def _disconnect(self, engine: PMDAEngine):
        engine.events.sequenceStarted.disconnect(self._onMDAStarted)
        engine.events.frameReady.disconnect(self._onMDAFrame)

    def disconnect(self):
        "Disconnect this writer from processing any more events"
        self._core.mda.events.sequenceStarted.disconnect(self._onMDAStarted)
        self._core.mda.events.frameReady.disconnect(self._onMDAFrame)

    @staticmethod
    def get_unique_folder(
        folder_base_name: Union[str, Path],
        suffix: Union[str, Path] = None,
        create: bool = False,
    ) -> Path:
        """
        Get a unique foldername of the form '{folder_base_name}_{i}

        Parameters
        ----------
        folder_base_name : str or Path
            The folder name in which to put data
        suffix : str or Path
            If given, to be used as the path suffix. e.g. `.zarr`
        create : bool, default False
            Whether to create the folder.
        '"""
        folder = Path(folder_base_name).resolve()
        stem = str(folder.stem)

        def new_path(i):
            path = folder.parent / (stem + f"_{i}")
            if suffix:
                return path.with_suffix(suffix)
            return path

        i = 1
        path = new_path(i)
        while path.exists():
            i += 1
            path = new_path(i)
        if create:
            path.mkdir(parents=True)
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

    @staticmethod
    def event_to_index(axis_order: Sequence[str], event: MDAEvent) -> Tuple[int, ...]:
        return tuple(event.index[a] for a in axis_order)


class SimpleMultiFileTiffWriter(BaseWriter):
    def __init__(
        self, data_folder_name: Union[str, Path], core: CMMCorePlus = None
    ) -> None:
        if tifffile is None:
            raise ValueError(
                "This writer requires tifffile to be installed. "
                "Try: `pip install tifffile`"
            )
        super().__init__(core)
        self._data_folder_name = data_folder_name

    def _onMDAStarted(self, sequence: MDASequence) -> None:
        self._path = self.get_unique_folder(self._data_folder_name, create=True)
        self._axis_order = self.sequence_axis_order(sequence)
        with open(self._path / "useq-sequence.json", "w") as f:
            f.write(sequence.json())

    def _onMDAFrame(self, img: np.ndarray, event: MDASequence) -> None:
        index = self.event_to_index(self._axis_order, event)
        name = (
            "_".join(
                [
                    self._axis_order[i] + f"{index[i]}".zfill(3)
                    for i in range(len(index))
                ]
            )
            + ".tiff"
        )
        tifffile.imwrite(self._path / name, img)


class ZarrWriter(BaseWriter):
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
        if zarr is None:
            raise ValueError(
                "This writer requires zarr to be installed. Try: `pip install zarr`"
            )
        super().__init__(core)

        self._store_name = str(store_name)
        self._img_shape = img_shape
        self._dtype = dtype

    def _onMDAStarted(self, sequence: MDASequence):
        self._axis_order = self.sequence_axis_order(sequence)

        name = self.get_unique_folder(self._store_name, suffix=".zarr")
        assert isinstance(name, (Path, str))
        self._z = zarr.open(
            name,
            # self._store_name.format(run=self._run_number),
            mode="w",
            shape=sequence.shape + self._img_shape,
            dtype=self._dtype,
        )
        self._z.attrs["axis_order"] = sequence.axis_order + "yx"
        self._z.attrs["useq-sequence"] = sequence.json()

    def _onMDAFrame(self, img: np.ndarray, event: MDAEvent):
        self._z[self.event_to_index(self._axis_order, event)] = img
