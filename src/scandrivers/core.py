from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd


class DeviceDriver(ABC):
    """Base interface for loading data from a specific device output format."""

    name: str = ""

    @abstractmethod
    def load(self, path: str | Path, *, scan_mode: str = "scan") -> pd.DataFrame:
        """Load device data from a path and return a DataFrame."""


_DRIVERS: dict[str, DeviceDriver] = {}


def register_driver(driver: DeviceDriver) -> None:
    """Register a device driver by name."""
    if not driver.name:
        raise ValueError("Driver name must be set")
    _DRIVERS[driver.name.lower()] = driver


def get_driver(name: str) -> DeviceDriver:
    """Return a registered driver by name."""
    key = name.lower()
    if key not in _DRIVERS:
        raise KeyError(f"Unknown driver: {name}")
    return _DRIVERS[key]


def list_drivers() -> list[str]:
    """Return the registered driver names."""
    return sorted(_DRIVERS)


def load_data(
    path: str | Path,
    driver: str | DeviceDriver | None = None,
    *,
    scan_mode: str = "scan",
) -> pd.DataFrame:
    """Load data using a registered driver or the supplied driver instance."""
    if isinstance(driver, DeviceDriver):
        selected_driver = driver
    elif isinstance(driver, str):
        selected_driver = get_driver(driver)
    elif driver is None:
        raise ValueError("A driver name or instance is required")
    else:
        raise TypeError("driver must be a string name or DeviceDriver instance")

    return selected_driver.load(path, scan_mode=scan_mode)
