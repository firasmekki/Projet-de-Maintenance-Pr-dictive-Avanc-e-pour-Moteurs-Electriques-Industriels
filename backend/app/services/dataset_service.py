"""Parse, validate and summarise uploaded sensor datasets."""
from __future__ import annotations

import io
import json
import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Column name normalisation
# ---------------------------------------------------------------------------

_COLUMN_MAP: dict[str, list[str]] = {
    "timestamp":    ["timestamp", "time", "datetime", "date", "ts"],
    "temperature":  ["temperature", "temp", "temperature_c", "temp_c"],
    "vibration":    ["vibration", "vib", "vibration_mms", "vib_mms", "acceleration"],
    "current":      ["current", "curr", "current_a", "i", "amp", "amps", "i_rms"],
    "voltage":      ["voltage", "volt", "voltage_v", "u", "v_rms"],
    "power":        ["power", "pwr", "power_kw", "kw", "active_power"],
    "power_factor": ["power_factor", "pf", "cos_phi", "powerfactor"],
    "thd":          ["thd", "total_harmonic_distortion", "harmonic"],
    "load":         ["load", "load_pct", "load_percent", "load_%", "utilization"],
}

_REQUIRED_ANY = {"temperature", "vibration", "current"}
_NUMERIC_COLS  = {"temperature", "vibration", "current", "voltage",
                  "power", "power_factor", "thd", "load"}


class DatasetValidationError(ValueError):
    """Raised when the uploaded file cannot be parsed or lacks required columns."""


class DatasetService:
    """Parse, validate, clean and summarise an uploaded dataset."""

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def process(
        self,
        content: bytes,
        filename: str,
    ) -> dict[str, Any]:
        """
        Parse the file, validate columns, compute quality metrics.

        Returns a dict with keys:
          row_count, column_count, missing_values, quality_score,
          columns (list[str]), records (list[dict]), preview (list[dict])
        """
        df = self._parse(content, filename)
        df = self._normalise_columns(df)
        self._validate_columns(df)
        df = self._coerce_types(df)
        return self._build_summary(df)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse(self, content: bytes, filename: str) -> pd.DataFrame:
        ext = filename.rsplit(".", 1)[-1].lower()
        try:
            if ext == "csv":
                df = pd.read_csv(io.BytesIO(content))
            elif ext in ("xlsx", "xls"):
                df = pd.read_excel(io.BytesIO(content))
            elif ext == "json":
                data = json.loads(content)
                df = pd.DataFrame(data if isinstance(data, list) else [data])
            else:
                raise DatasetValidationError(f"Unsupported file format: .{ext}")
        except (pd.errors.ParserError, ValueError, Exception) as exc:
            raise DatasetValidationError(f"Could not parse file: {exc}") from exc

        if df.empty:
            raise DatasetValidationError("Uploaded file contains no data rows.")
        return df

    # ------------------------------------------------------------------
    # Column normalisation
    # ------------------------------------------------------------------

    def _normalise_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        rename: dict[str, str] = {}
        lowered = {c.lower().strip().replace(" ", "_"): c for c in df.columns}
        for canonical, aliases in _COLUMN_MAP.items():
            for alias in aliases:
                if alias in lowered and canonical not in rename.values():
                    rename[lowered[alias]] = canonical
                    break
        return df.rename(columns=rename)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_columns(self, df: pd.DataFrame) -> None:
        present = set(df.columns)
        if not present & _REQUIRED_ANY:
            raise DatasetValidationError(
                f"Dataset must contain at least one of: {sorted(_REQUIRED_ANY)}. "
                f"Found columns: {sorted(present)}"
            )

    # ------------------------------------------------------------------
    # Type coercion
    # ------------------------------------------------------------------

    def _coerce_types(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in _NUMERIC_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df.sort_values("timestamp").reset_index(drop=True)

        return df

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _build_summary(self, df: pd.DataFrame) -> dict[str, Any]:
        total_cells = df.shape[0] * df.shape[1]
        missing = int(df.isnull().sum().sum())
        quality = round(100.0 * (1.0 - missing / max(total_cells, 1)), 2)

        # Serialise timestamps before JSON dump
        records_df = df.copy()
        if "timestamp" in records_df.columns:
            records_df["timestamp"] = records_df["timestamp"].astype(str)

        records: list[dict] = records_df.where(pd.notnull(records_df), None).to_dict(orient="records")
        preview  = records[:50]

        return {
            "row_count":      int(df.shape[0]),
            "column_count":   int(df.shape[1]),
            "missing_values": missing,
            "quality_score":  quality,
            "columns":        list(df.columns),
            "records":        records,
            "preview":        preview,
        }
