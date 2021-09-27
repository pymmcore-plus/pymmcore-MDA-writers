try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"
__author__ = "Ian Hunt-Isaak"
__email__ = "ianhuntisaak@gmail.com"

from ._writers import zarr_MDA_writer

__all__ = [
    "__version__",
    "zarr_MDA_writer",
]
