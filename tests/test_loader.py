from pathlib import Path

import pandas as pd
import pytest

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


# pXRF Driver Tests
class TestPxrfDriver:
    """Tests for the pXRF driver."""

    @pytest.fixture
    def pxrf_data_dir(self):
        """Return the pXRF finalized data directory."""
        return Path(__file__).resolve().parents[1] / "data" / "pxrf" / "Final"

    @pytest.fixture
    def pxrf_xlsx_path(self, pxrf_data_dir):
        """Return the path to the pXRF Excel workbook."""
        path = pxrf_data_dir / "pXRF Readings (Trench1to6).xlsx"
        if not path.exists():
            pytest.skip("pXRF finalized data not available")
        return path

    @pytest.fixture
    def pxrf_ndt_path(self, pxrf_data_dir):
        """Return the path to the native pXRF .ndt file."""
        path = pxrf_data_dir / "pXRF Readings (Trench1to6).ndt"
        if not path.exists():
            pytest.skip("pXRF native .ndt file not available")
        return path

    def test_pxrf_driver_registered(self):
        """Verify that the pXRF driver is registered."""
        assert "pxrf" in list_drivers()
        driver = get_driver("pxrf")
        assert driver.name == "pxrf"

    def test_load_pxrf_xlsx_file(self, pxrf_xlsx_path):
        """Test loading a pXRF Excel export."""
        df = load_data(pxrf_xlsx_path, driver="pxrf")

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        # Verify expected metadata columns
        assert "reading_no" in df.columns
        assert "time" in df.columns
        assert "duration" in df.columns
        assert "units" in df.columns
        assert "sample" in df.columns
        assert "test_type" in df.columns
        # Verify expected element columns
        assert "mo" in df.columns  # Mo normalized to lowercase
        assert "zr" in df.columns  # Zr
        assert "fe" in df.columns  # Fe

    def test_pxrf_row_count(self, pxrf_xlsx_path):
        """Verify the pXRF file has the expected number of rows."""
        df = load_data(pxrf_xlsx_path, driver="pxrf")
        # 366 data rows expected
        assert len(df) == 366

    def test_pxrf_column_normalization(self, pxrf_xlsx_path):
        """Verify columns are normalized to snake_case."""
        df = load_data(pxrf_xlsx_path, driver="pxrf")
        
        # Check that original format doesn't appear
        assert "Reading No" not in df.columns
        assert "reading_no" in df.columns
        
        assert "Test Type" not in df.columns
        assert "test_type" in df.columns
        
        # Element columns normalized
        assert "Mo CPS/ua" not in df.columns
        assert "mo_cps_ua" in df.columns
        
        assert "Zr Error" not in df.columns
        assert "zr_error" in df.columns

    def test_pxrf_dtypes(self, pxrf_xlsx_path):
        """Verify proper dtypes for columns."""
        df = load_data(pxrf_xlsx_path, driver="pxrf")
        
        # Metadata dtypes
        assert df["reading_no"].dtype in ["Int64", "int64"]
        assert pd.api.types.is_datetime64_any_dtype(df["time"])
        assert df["duration"].dtype in ["float32", "float64"]
        # Units can be object or StringDtype
        assert df["units"].dtype in ["object", "string"]
        
        # Element measurement columns should be float or contain <LOD strings
        # (handled as object because of mixed numeric/<LOD values)
        mo_dtype = df["mo"].dtype
        assert mo_dtype in ["float32", "float64", "object"]

    def test_pxrf_units_preserved(self, pxrf_xlsx_path):
        """Verify that units (ppm vs %) are preserved."""
        df = load_data(pxrf_xlsx_path, driver="pxrf")
        
        # Should have both ppm and % readings
        unique_units = df["units"].unique()
        assert "ppm" in unique_units
        assert "%" in unique_units

    def test_pxrf_lod_values_preserved(self, pxrf_xlsx_path):
        """Verify that <LOD values are preserved and not converted to NaN."""
        df = load_data(pxrf_xlsx_path, driver="pxrf")
        
        # Look for <LOD strings in element columns
        lod_count = 0
        for col in df.columns:
            if col not in [
                "reading_no", "time", "duration", "units", "sequence", 
                "flags", "sample", "test_type"
            ]:
                # Count <LOD values (case-insensitive)
                lod_in_col = sum(
                    1 for val in df[col]
                    if isinstance(val, str) and "<lod" in val.lower()
                )
                lod_count += lod_in_col
        
        # Expect significant number of <LOD values
        assert lod_count > 0

    def test_pxrf_ndt_resolves_to_xlsx_sidecar(self, pxrf_ndt_path, pxrf_xlsx_path):
        """Test that .ndt files are resolved to .xlsx sidecars."""
        df_from_ndt = load_data(pxrf_ndt_path, driver="pxrf")
        df_from_xlsx = load_data(pxrf_xlsx_path, driver="pxrf")
        
        # Should produce identical results (same number of rows and columns)
        assert df_from_ndt.shape == df_from_xlsx.shape
        assert list(df_from_ndt.columns) == list(df_from_xlsx.columns)

    def test_pxrf_ndt_without_sidecar_raises_error(self, tmp_path):
        """Test that an .ndt file without a sidecar raises a helpful error."""
        # Create a dummy .ndt file without a corresponding .xlsx/.xls
        ndt_path = tmp_path / "test_no_sidecar.ndt"
        ndt_path.write_bytes(b"dummy ndt content")
        
        with pytest.raises(FileNotFoundError, match="No Excel sidecar"):
            load_data(ndt_path, driver="pxrf")

    def test_pxrf_unsupported_format_raises_error(self):
        """Test that unsupported file formats raise an error."""
        csv_path = Path("/tmp/test.csv")
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            load_data(csv_path, driver="pxrf")

    def test_pxrf_metadata_columns(self, pxrf_xlsx_path):
        """Verify metadata columns are present and correctly parsed."""
        df = load_data(pxrf_xlsx_path, driver="pxrf")
        
        # Check metadata columns exist
        metadata_cols = ["reading_no", "time", "duration", "units", "sequence", 
                         "flags", "sample", "test_type"]
        for col in metadata_cols:
            assert col in df.columns, f"Missing metadata column: {col}"
        
        # Verify some values
        assert df["reading_no"].iloc[0] >= 1  # Valid reading number
        assert df["time"].iloc[0] is not pd.NaT  # Valid timestamp
        assert df["duration"].iloc[0] > 0  # Valid duration
        assert df["units"].iloc[0] in ["ppm", "%"]  # Valid unit

    def test_pxrf_element_columns(self, pxrf_xlsx_path):
        """Verify element measurement columns are present."""
        df = load_data(pxrf_xlsx_path, driver="pxrf")
        
        # Check for common elements and their associated columns
        expected_elements = {
            "mo": ["mo", "mo_error", "mo_cps_ua"],
            "zr": ["zr", "zr_error", "zr_cps_ua"],
            "fe": ["fe", "fe_error", "fe_cps_ua"],
            "ca": ["ca", "ca_error", "ca_cps_ua"],
        }
        
        for element, cols in expected_elements.items():
            for col in cols:
                assert col in df.columns, f"Missing column: {col}"

