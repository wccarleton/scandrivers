from pathlib import Path

import pandas as pd
import pytest

from scandrivers import DeviceDriver, demo_data_path, get_driver, list_drivers, load_data, register_driver


def test_load_data_with_kt20_driver_returns_expected_columns():
    data_path = demo_data_path("kt20", "kt20_0467", "117", "record_scanner_10khz_117.csv")
    df = load_data(data_path, driver="kt20")

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert {"record_id", "date", "time", "frequency", "pin", "diameter_correction"}.issubset(df.columns)
    assert df["record_id"].iloc[0] == 117
    assert df["frequency"].iloc[0] == "10kHz"
    assert df["susceptibility_10_3si"].dtype.kind in {"f", "i"}
    assert "kt20" in list_drivers()


def test_load_data_aggregates_scan_files_from_directory():
    data_dir = demo_data_path("kt20", "kt20_0467")
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
    assert "source" in df.columns


class TestPxrfDriver:
    @pytest.fixture
    def pxrf_data_dir(self):
        return demo_data_path("pxrf", "Final")

    @pytest.fixture
    def pxrf_xlsx_path(self, pxrf_data_dir):
        path = pxrf_data_dir / "pXRF Readings (Trench1to6).xlsx"
        if not path.exists():
            pytest.skip(f"Demo data not found: {path}")
        return path

    @pytest.fixture
    def pxrf_ndt_path(self, pxrf_data_dir):
        path = pxrf_data_dir / "pXRF Readings (Trench1to6).ndt"
        if not path.exists():
            pytest.skip(f"Demo data not found: {path}")
        return path

    def test_pxrf_driver_registered(self):
        assert "pxrf" in list_drivers()
        driver = get_driver("pxrf")
        assert driver.name == "pxrf"

    def test_load_pxrf_xlsx_file(self, pxrf_xlsx_path):
        df = load_data(pxrf_xlsx_path, driver="pxrf")
        assert isinstance(df, pd.DataFrame)
        assert not df.empty

        # Check for metadata columns
        assert "reading_no" in df.columns
        assert "time" in df.columns
        assert "duration" in df.columns
        assert "units" in df.columns
        assert "sample" in df.columns
        assert "test_type" in df.columns

        # Check for element columns
        assert "mo" in df.columns
        assert "zr" in df.columns
        assert "fe" in df.columns

    def test_pxrf_row_count(self, pxrf_xlsx_path):
        df = load_data(pxrf_xlsx_path, driver="pxrf")
        assert len(df) == 366

    def test_pxrf_column_normalization(self, pxrf_xlsx_path):
        df = load_data(pxrf_xlsx_path, driver="pxrf")

        # Check original format headers are not present
        assert "Reading No" not in df.columns
        assert "reading_no" in df.columns

        assert "Mo CPS/ua" not in df.columns
        assert "mo_cps_ua" in df.columns

    def test_pxrf_dtypes(self, pxrf_xlsx_path):
        df = load_data(pxrf_xlsx_path, driver="pxrf")

        # Check reading_no is integer
        assert df["reading_no"].dtype.kind == "i"

        # Check time is datetime
        assert pd.api.types.is_datetime64_any_dtype(df["time"])

        # Check duration is float
        assert df["duration"].dtype.kind == "f"

        # Check units is object/string
        assert df["units"].dtype.kind in {"O", "U"}

    def test_pxrf_units_preserved(self, pxrf_xlsx_path):
        df = load_data(pxrf_xlsx_path, driver="pxrf")

        unique_units = df["units"].unique()
        assert len(unique_units) > 1
        assert "ppm" in unique_units
        assert "%" in unique_units

    def test_pxrf_lod_values_preserved(self, pxrf_xlsx_path):
        df = load_data(pxrf_xlsx_path, driver="pxrf")

        # Count <LOD values across all element columns
        lod_count = 0
        for col in df.columns:
            for val in df[col]:
                if isinstance(val, str) and "<lod" in val.lower():
                    lod_count += 1

        assert lod_count > 0

    def test_pxrf_ndt_resolves_to_xlsx_sidecar(self, pxrf_ndt_path, pxrf_xlsx_path):
        # Load from both .ndt (which resolves to .xlsx sidecar) and .xlsx directly
        df_from_ndt = load_data(pxrf_ndt_path, driver="pxrf")
        df_from_xlsx = load_data(pxrf_xlsx_path, driver="pxrf")

        # Should have same shape and columns
        assert df_from_ndt.shape == df_from_xlsx.shape
        assert list(df_from_ndt.columns) == list(df_from_xlsx.columns)

    def test_pxrf_ndt_without_sidecar_raises_error(self, tmp_path):
        ndt_path = tmp_path / "test.ndt"
        ndt_path.write_text("dummy")

        with pytest.raises(FileNotFoundError, match="No Excel sidecar"):
            load_data(ndt_path, driver="pxrf")

    def test_pxrf_unsupported_format_raises_error(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("a,b\n1,2")

        with pytest.raises(ValueError, match="Unsupported file format"):
            load_data(csv_path, driver="pxrf")

    def test_pxrf_metadata_columns(self, pxrf_xlsx_path):
        df = load_data(pxrf_xlsx_path, driver="pxrf")

        metadata_cols = ["reading_no", "time", "duration", "units", "sample", "test_type"]
        for col in metadata_cols:
            assert col in df.columns
            assert not df[col].isna().all(), f"Column {col} is entirely null"

    def test_pxrf_element_columns(self, pxrf_xlsx_path):
        df = load_data(pxrf_xlsx_path, driver="pxrf")

        expected_elements = ["mo", "zr", "fe", "ca"]
        for element in expected_elements:
            assert element in df.columns
