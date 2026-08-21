"""Generic scan data loading framework with pluggable device drivers.

Developed by the Max Planck Institute for Geoanthropology (MPIGEA) for 
geoarchaeological and materials analysis workflows.
"""

from pathlib import Path

from .core import DeviceDriver, get_driver, list_drivers, load_data, register_driver
from .drivers.kt20 import KT20Driver
from .drivers.pxrf import PxrfDriver

register_driver(KT20Driver())
register_driver(PxrfDriver())

__all__ = [
    "DeviceDriver",
    "KT20Driver",
    "PxrfDriver",
    "demo_data_path",
    "get_driver",
    "list_drivers",
    "load_data",
    "register_driver",
]
__version__ = "0.1.0"


def demo_data_path(*parts):
    """Return path to demo data file.
    
    Usage:
        from scandrivers import demo_data_path
        
        # Get path to pXRF demo data
        pxrf_path = demo_data_path("pxrf", "Final", "pXRF Readings (Trench1to6).xlsx")
        
        # Get path to KT20 demo data
        kt20_path = demo_data_path("kt20", "kt20_0467", "289", "record_scanner_10khz_289.csv")
    
    Args:
        *parts: Path components to append to demo_data directory
    
    Returns:
        Path object pointing to demo data file
    """
    base = Path(__file__).parent / "demo_data"
    return base / Path(*parts)
