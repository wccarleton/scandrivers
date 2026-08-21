"""Generic scan data loading framework with pluggable device drivers."""

from .core import DeviceDriver, get_driver, list_drivers, load_data, register_driver
from .drivers.kt20 import KT20Driver
from .drivers.pxrf import PxrfDriver

register_driver(KT20Driver())
register_driver(PxrfDriver())

__all__ = [
    "DeviceDriver",
    "KT20Driver",
    "PxrfDriver",
    "get_driver",
    "list_drivers",
    "load_data",
    "register_driver",
]
__version__ = "0.1.0"
