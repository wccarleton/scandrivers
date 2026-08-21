# scandrivers

A Python package for loading structured lab instrument exports through pluggable device drivers. Developed by the Max Planck Institute for Geoanthropology (MPIGEA) for laboratory data workflows in geoarchaeology, materials analysis, and geochemistry.

## Features

- **Pluggable driver architecture**: Register custom drivers for different instrument formats
- **pandas DataFrame output**: All data loads into standard DataFrames for analysis
- **Demo data included**: Example datasets for each supported driver to get started quickly
- **Standardized metadata handling**: Consistent handling of units, detection limits, and metadata across drivers

## Supported Instruments

- **KT-20** (Kappabrdige): Magnetic susceptibility measurements with frequency-dependent analysis
- **pXRF** (portable X-ray fluorescence): Elemental composition analysis with detection limit tracking

## Quick Start

```python
from pathlib import Path
from scandrivers import load_data

# Load pXRF soil elemental analysis
pxrf_path = Path("scandrivers/demo_data/pxrf/Final/pXRF Readings (Trench1to6).xlsx")
df = load_data(pxrf_path, driver="pxrf")
print(df.head())

# Load KT-20 magnetic susceptibility measurements
kt20_path = Path("scandrivers/demo_data/kt20/kt20_0467/117/record_scanner_10khz_117.csv")
df = load_data(kt20_path, driver="kt20")
print(df.head())
```

## Installation

### From source (development mode)

```bash
git clone https://github.com/wccarleton/scandrivers.git
cd scandrivers
pip install -e .
```

## Documentation

The documentation site covers installation, supported devices, expected input formats, and executable notebook demos. It is built with Quarto and published to GitHub Pages.

Build the site locally with:

```bash
quarto render
```

The site source is organized in `index.qmd`, `getting-started.qmd`, `devices/`, and `notebooks/`.

Or with conda:

```bash
conda env create -n scandrivers python=3.11
conda activate scandrivers
pip install -e .
```

### Run tests

```bash
pytest tests/
```

### Explore demo notebooks

The `notebooks/` directory contains demonstration workflows:

- `notebooks/kt20_scan_demo.ipynb` - Magnetic susceptibility analysis workflow
- `notebooks/pxrf_scan_demo.ipynb` - pXRF elemental analysis with geoarchaeological context parsing

Start Jupyter and open these notebooks:

```bash
jupyter notebook notebooks/
```

## Creating Custom Drivers

Drivers inherit from the `DeviceDriver` ABC and implement a `load()` method:

```python
from scandrivers import DeviceDriver, register_driver
import pandas as pd

class MyInstrumentDriver(DeviceDriver):
    @property
    def name(self):
        return "myinstrument"
    
    def load(self, path, **kwargs):
        # Load your instrument data format
        df = pd.read_csv(path)
        return df

# Register it
register_driver(MyInstrumentDriver())

# Now usable via the package
from scandrivers import load_data
df = load_data("data.csv", driver="myinstrument")
```

## Authors

Developed at the Max Planck Institute for Geoanthropology (MPIGEA).

## License

See LICENSE file for details.
