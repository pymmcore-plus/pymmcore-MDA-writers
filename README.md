# pymmcore-MDA-writers

[![License](https://img.shields.io/pypi/l/pymmcore-MDA-writers.svg?color=green)](https://github.com/ianhi/pymmcore-MDA-writers/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/pymmcore-MDA-writers.svg?color=green)](https://pypi.org/project/pymmcore-MDA-writers)
[![Python Version](https://img.shields.io/pypi/pyversions/pymmcore-MDA-writers.svg?color=green)](https://python.org)
[![Test](https://github.com/ianhi/pymmcore-MDA-writers/actions/workflows/ci.yml/badge.svg)](https://github.com/ianhi/mpl-interactions/actions/)
[![codecov](https://codecov.io/gh/ianhi/pymmcore-MDA-writers/branch/main/graph/badge.svg)](https://codecov.io/gh/ianhi/pymmcore-MDA-writers)

This package provides writers for [pymmcore-plus](https://pymmcore-plus.readthedocs.io). At the time of writing pymmc+ provides hooks for saving images but does not implement
any mechanism for saving image (check in https://github.com/tlambert03/pymmcore-plus/pull/29 for updates). Currently provided are:

1. A simple multifile tiff writer - can be loaded with `tifffile`
2. A simple zarr writer - not ome-zarr

```bash
pip install pymmcore-mda-writers
```

(This will require a minimum of pymmcore-plus>=0.4.0 which has not yet been released. You can install a working version with `pip install git+https://github.com/tlambert03/pymmcore-plus`)


All you need to add to your script is:
```python
# tiff writer
writer = SimpleMultiFileTiffWriter("data/tiff_writer_example/run")

# zarr writer
writer = ZarrWriter("data/zarr_writer_example/run", img_shape=(512, 512), dtype=np.uint16)
```

for a complete example see the examples folder.
