from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from ..core import DeviceDriver


class PxrfDriver(DeviceDriver):
    """Driver for loading pXRF (portable X-ray fluorescence) data from Niton exports.
    
    Supports:
    - Direct loading of .xlsx and .xls Excel exports from Niton XL3t instruments
    - Resolution of native .ndt files to corresponding .xlsx/.xls sidecars
    
    The .ndt format is a proprietary binary database from Thermo Scientific Niton.
    Public documentation describes exports but does not provide a parsing specification.
    Therefore, .ndt files are supported by resolving to a corresponding exported workbook.
    """

    name = "pxrf"

    def load(self, path: str | Path, *, scan_mode: str = "scan") -> pd.DataFrame:
        """Load pXRF data from an Excel export or resolve from native .ndt file.
        
        Args:
            path: Path to .xlsx, .xls, or .ndt file
            scan_mode: Currently unused; present for interface compatibility
            
        Returns:
            DataFrame with normalized columns and proper dtypes
            
        Raises:
            FileNotFoundError: If path does not exist or .ndt has no sidecar
            ValueError: If file format is unsupported
        """
        file_path = Path(path)
        
        # Resolve .ndt files to their .xlsx/.xls sidecars
        if file_path.suffix.lower() == ".ndt":
            file_path = self._resolve_ndt_sidecar(file_path)
        
        return self._load_workbook(file_path)

    def _resolve_ndt_sidecar(self, ndt_path: Path) -> Path:
        """Resolve an .ndt file to its corresponding .xlsx or .xls sidecar.
        
        Args:
            ndt_path: Path to the .ndt file
            
        Returns:
            Path to the resolved sidecar file
            
        Raises:
            FileNotFoundError: If no sidecar is found
        """
        if not ndt_path.exists():
            raise FileNotFoundError(f"File not found: {ndt_path}")
        
        base_stem = ndt_path.stem  # Remove .ndt extension
        base_dir = ndt_path.parent
        
        # Look for .xlsx first, then .xls
        for ext in [".xlsx", ".xls"]:
            candidate = base_dir / f"{base_stem}{ext}"
            if candidate.exists():
                return candidate
        
        raise FileNotFoundError(
            f"No Excel sidecar (.xlsx or .xls) found for native .ndt file: {ndt_path}\n"
            f"Expected one of: {base_dir / (base_stem + '.xlsx')} or {base_dir / (base_stem + '.xls')}"
        )

    def _load_workbook(self, path: Path) -> pd.DataFrame:
        """Load data from an Excel workbook.
        
        Args:
            path: Path to .xlsx or .xls file
            
        Returns:
            DataFrame with normalized columns and proper dtypes
            
        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file format is unsupported
        """
        suffix = path.suffix.lower()
        if suffix not in [".xlsx", ".xls"]:
            raise ValueError(f"Unsupported file format: {suffix}. Expected .xlsx, .xls, or .ndt")
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        # Determine engine based on file extension
        engine = "openpyxl" if suffix == ".xlsx" else "xlrd"
        
        # Load the Excel file
        df = pd.read_excel(path, sheet_name=0, engine=engine)
        
        # Normalize column names to snake_case
        df.columns = [self._normalize_column_name(col) for col in df.columns]
        
        # Apply type conversions and ensure proper dtypes
        df = self._apply_dtypes(df)
        
        return df

    def _normalize_column_name(self, name: str) -> str:
        """Normalize a column name to snake_case.
        
        Handles various patterns:
        - "Reading No" → "reading_no"
        - "Mo Error" → "mo_error"
        - "Mo CPS/ua" → "mo_cps_ua"
        - Trailing/leading spaces are stripped
        - Multiple consecutive underscores are collapsed
        """
        # Strip leading/trailing whitespace
        stripped = name.strip()
        
        # Convert to lowercase and replace non-alphanumeric with underscore
        # Preserve spaces that should become underscores
        converted = re.sub(r"[^a-z0-9]+", "_", stripped.lower())
        
        # Remove leading/trailing underscores
        normalized = converted.strip("_")
        
        return normalized

    def _apply_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply proper dtypes to columns.
        
        Metadata columns:
        - reading_no: int64
        - time: datetime64[ns]
        - duration: float64
        - units: object (preserved as-is: ppm or %)
        - sequence, flags, sample, test_type: object
        
        Element columns:
        - Concentration values: handled as objects (may contain <LOD or float)
        - Error and CPS columns: float64 (LOD preserved where applicable)
        """
        # Convert reading_no to int
        if "reading_no" in df.columns:
            df["reading_no"] = pd.to_numeric(df["reading_no"], errors="coerce").astype("Int64")
        
        # Convert time to datetime if present
        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"], errors="coerce")
        
        # Convert duration to float
        if "duration" in df.columns:
            df["duration"] = pd.to_numeric(df["duration"], errors="coerce")
        
        # For all other numeric columns (element measurements), attempt conversion
        # but preserve <LOD strings and handle None/NaN gracefully
        for col in df.columns:
            if col in ["reading_no", "time", "duration", "units", "sequence", "flags", "sample", "test_type"]:
                continue
            
            # For Error and CPS columns, convert to float (None becomes NaN)
            if "error" in col.lower() or "cps" in col.lower():
                df[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                # For concentration columns, preserve <LOD strings but convert numeric values
                df[col] = df[col].apply(self._convert_element_value)
        
        return df

    def _convert_element_value(self, value: Any) -> Any:
        """Convert an element concentration value.
        
        - Preserves <LOD strings
        - Converts numeric values to float
        - Handles None/NaN
        """
        if value is None or pd.isna(value):
            return value
        
        if isinstance(value, str):
            # Preserve <LOD markers
            if "<lod" in value.lower().strip():
                return value
            # Try to convert to float
            try:
                return float(value)
            except ValueError:
                return value
        
        # Already numeric
        try:
            return float(value)
        except (ValueError, TypeError):
            return value
