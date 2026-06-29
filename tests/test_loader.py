from pathlib import Path

import pandas as pd

from scandrivers import DeviceDriver, get_driver, list_drivers, load_data, register_driver


def test_load_data_with_kt20_driver_returns_expected_columns():
    data_dir = Path(__file__).resolve().parents[1] / "data" / "kt20" / "kt20_0467" / "117"
    df = load_data(data_dir / "record_scanner_10khz_117.csv", driver="kt20")

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert {"record_id", "date", "time", "frequency", "pin", "diameter_correction"}.issubset(df.columns)
    assert df["record_id"].iloc[0] == 117
    assert df["frequency"].iloc[0] == "10kHz"
    assert df["susceptibility_10_3si"].dtype.kind in {"f", "i"}
    assert "kt20" in list_drivers()


def test_load_data_aggregates_scan_files_from_directory():
    data_dir = Path(__file__).resolve().parents[1] / "data" / "kt20" / "kt20_0467"
    df = load_data(data_dir, driver="kt20", scan_mode="scan")

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df["record_id"].nunique() >= 2


def test_register_driver_allows_custom_loader():
    class ExampleDriver(DeviceDriver):
        name = "example"

        def load(self, path, *, scan_mode="scan"):
            return pd.DataFrame({"source": [str(path)]})

    register_driver(ExampleDriver())
    df = load_data(Path("demo.csv"), driver="example")

    assert isinstance(df, pd.DataFrame)
    assert df["source"].iloc[0] == "demo.csv"
    assert get_driver("example").name == "example"
