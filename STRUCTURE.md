# scandrivers Package Structure

## Overview

`scandrivers` is a standalone Python package for loading structured lab instrument exports through pluggable device drivers. Developed by the Max Planck Institute for Geoanthropology (MPIGEA), it's designed to support the lab's geoarchaeological, materials analysis, and geochemistry workflows.

## Core Concepts

### Device Drivers

Drivers inherit from `DeviceDriver` ABC and implement a `load()` method. Each driver is responsible for:

- Parsing instrument-specific file formats
- Normalizing column names (e.g., "Reading No" → "reading_no")
- Applying appropriate data types (datetime, int, float, etc.)
- Handling instrument-specific quirks (e.g., <LOD values in pXRF)

**Registered drivers:**
- `kt20`: Loads KT-20 magnetic susceptibility CSV exports
- `pxrf`: Loads pXRF elemental composition (.xlsx, .xls, or .ndt with sidecar)

### Data Loading API

```python
from scandrivers import load_data, demo_data_path

# Load demo data
pxrf_path = demo_data_path("pxrf", "Final", "pXRF Readings (Trench1to6).xlsx")
df = load_data(pxrf_path, driver="pxrf")

# Load from custom path
df = load_data("path/to/your/data.xlsx", driver="pxrf")
```

### Demo Data Access

The `demo_data_path()` helper makes it easy to reference included datasets:

```python
from scandrivers import demo_data_path

# KT-20 data
kt20_path = demo_data_path("kt20", "kt20_0467", "289", "record_scanner_10khz_289.csv")

# pXRF data
pxrf_path = demo_data_path("pxrf", "Final", "pXRF Readings (Trench1to6).xlsx")
```

## Installation

### Development (editable install)

```bash
git clone https://github.com/wccarleton/scandrivers.git
cd scandrivers
pip install -e .
```

### Run tests

```bash
pytest tests/ -v
```

### Explore notebooks

```bash
jupyter notebook notebooks/
```

## Creating Custom Drivers

To add a new driver for a different instrument:

1. Create a new file in `src/scandrivers/drivers/` (e.g., `myinstrument.py`)
2. Inherit from `DeviceDriver` and implement `load()`
3. Register the driver in `src/scandrivers/__init__.py`

Example:

```python
# src/scandrivers/drivers/myinstrument.py
from .core import DeviceDriver
import pandas as pd

class MyInstrumentDriver(DeviceDriver):
    @property
    def name(self):
        return "myinstrument"
    
    def load(self, path, **kwargs):
        # Parse your instrument format
        df = pd.read_csv(path, ...)
        # Normalize columns, apply dtypes, etc.
        return df

# src/scandrivers/__init__.py
from .drivers.myinstrument import MyInstrumentDriver
register_driver(MyInstrumentDriver())
```

## Integration with Other Projects

`scandrivers` is designed to be imported into other analysis projects:

```bash
# In your project's environment
pip install git+https://github.com/wccarleton/scandrivers.git

# In your analysis code
from scandrivers import load_data, demo_data_path

# Load data from your own file paths
df = load_data("path/to/your/pxrf_export.xlsx", driver="pxrf")
```

## Testing

The test suite includes:

- **KT20 tests** (3): File loading, directory aggregation, custom drivers
- **pXRF tests** (12): File format support, column normalization, dtype validation, unit preservation, <LOD handling, .ndt sidecar resolution, error handling

All tests pass with:
```bash
pytest tests/test_loader.py -v
```

## Notes for MPIGEA Lab Use

- **pXRF driver**: Specifically handles geoarchaeological soil samples with sample code parsing (e.g., 'KKT1-0CM' → site=KK, trench=T1, depth=0cm)
- **<LOD preservation**: The pXRF driver intentionally preserves "<LOD" (less-than limit of detection) strings rather than converting to NaN, preserving measurement information
- **Unit handling**: pXRF data distinguishes between soil (ppm) and mining (%) measurements; both are preserved in the "units" column

## License

MIT License - See LICENSE file for details.

## Developed by

Max Planck Institute for Geoanthropology (MPIGEA)
