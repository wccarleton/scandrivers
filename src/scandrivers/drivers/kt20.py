from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import pandas as pd

from ..core import DeviceDriver

_METADATA_ALIASES = {
    "Record_ID": "record_id",
    "Record Id": "record_id",
    "Date": "date",
    "Time": "time",
    "Frequency": "frequency",
    "Pin": "pin",
    "Diameter corr.": "diameter_correction",
    "Diameter correction": "diameter_correction",
    "Measurement Type": "measurement_type",
    "Density": "density",
    "Picture": "picture",
    "Voice note": "voice_note",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "Altitude": "altitude",
    "Text Note": "text_note",
}


class KT20Driver(DeviceDriver):
    name = "kt20"

    def load(self, path: str | Path, *, scan_mode: str = "scan") -> pd.DataFrame:
        scan_path = Path(path)

        if scan_path.is_dir() and scan_mode == "scan":
            scan_files = sorted(scan_path.glob("**/record_scanner_*.csv"))
            if not scan_files:
                raise FileNotFoundError(f"No KT20 scan CSV files were found in {scan_path}")
            frames = [self._load_single_scan(path=scan_file) for scan_file in scan_files]
            return pd.concat(frames, ignore_index=True)

        return self._load_single_scan(path=scan_path)

    def _load_single_scan(self, path: str | Path) -> pd.DataFrame:
        scan_path = Path(path)
        metadata, rows = self._parse_scan_file(scan_path)
        df = pd.DataFrame(rows)

        for key, value in metadata.items():
            df[key] = value

        numeric_metadata_columns = {"record_id", "latitude", "longitude", "altitude"}
        for column in numeric_metadata_columns:
            if column in df.columns:
                df[column] = pd.to_numeric(df[column], errors="coerce")

        df["measurement_index"] = pd.to_numeric(df["measurement_index"], errors="coerce")
        df["susceptibility_10_3si"] = pd.to_numeric(df["susceptibility_10_3si"], errors="coerce")
        df["trigger_data"] = pd.to_numeric(df["trigger_data"], errors="coerce")

        metadata_columns = [
            column
            for column in [
                "record_id",
                "date",
                "time",
                "frequency",
                "pin",
                "diameter_correction",
                "measurement_type",
                "density",
                "picture",
                "voice_note",
                "latitude",
                "longitude",
                "altitude",
                "text_note",
            ]
            if column in df.columns
        ]
        data_columns = ["measurement_index", "susceptibility_10_3si", "trigger_data"]
        return df[metadata_columns + data_columns]

    def _normalize_name(self, name: str) -> str:
        stripped = name.strip()
        if stripped in _METADATA_ALIASES:
            return _METADATA_ALIASES[stripped]
        return re.sub(r"[^a-z0-9]+", "_", stripped.lower()).strip("_")

    def _parse_scan_file(self, path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        lines = [line.rstrip("\n") for line in path.read_text(encoding="utf-8-sig").splitlines()]
        if len(lines) < 3:
            raise ValueError(f"Expected a KT20 scan file with metadata and data rows: {path}")

        header = next(csv.reader([lines[0]]))
        values = next(csv.reader([lines[1]]))
        if len(header) != len(values):
            size = min(len(header), len(values))
            header = header[:size]
            values = values[:size]

        metadata = {
            self._normalize_name(column): (value.strip() if isinstance(value, str) else value)
            for column, value in zip(header, values)
        }

        rows: list[dict[str, Any]] = []
        for line in lines[2:]:
            if not line.strip():
                continue

            stripped = line.strip()
            if stripped.startswith(",Susceptibility") or stripped.startswith("Susceptibility"):
                continue
            if stripped.startswith(",Min,Max,Avg") or stripped.startswith("Kappa[") or stripped.startswith("Sigma["):
                continue
            if stripped.startswith("Record_ID") or stripped.startswith("Record_Id"):
                continue

            row = next(csv.reader([line]))
            if len(row) < 4:
                continue

            first = row[0].strip()
            if first.isdigit():
                rows.append(
                    {
                        "measurement_index": int(first),
                        "susceptibility_10_3si": row[1].strip(),
                        "trigger_data": row[3].strip(),
                    }
                )

        if not rows:
            raise ValueError(f"No scan measurement rows were found in {path}")

        return metadata, rows
