# scandrivers

scandrivers is a small Python package for loading structured lab instrument exports through pluggable device drivers.

## Example

```python
from pathlib import Path
from scandrivers import load_data

scan_path = Path("data/kt20/kt20_0467/117/record_scanner_10khz_117.csv")
df = load_data(scan_path, driver="kt20")
print(df.head())
```

Sample data for supported drivers lives under [data](data).

## Installation from GitHub

Install the latest version directly from GitHub:

```bash
git clone https://github.com/wccarleton/scandrivers.git
cd scandrivers
pip install -e .
```

If you are using a conda environment, activate it first and then run the install command above.

## Features

- Register device-specific loaders as drivers
- Load data through a common API
- Add new drivers without rewriting your analysis code
