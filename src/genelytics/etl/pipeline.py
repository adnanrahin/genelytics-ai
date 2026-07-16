from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import pandas as pd
from sqlalchemy.engine import Engine


class PandasETLPipeline:
    """Pandas helpers for chat-driven ETL."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self._frames: dict[str, pd.DataFrame] = {}
        self._active: Optional[str] = None

    @property
    def active_name(self) -> Optional[str]:
        return self._active

    def load_csv(self, path: str, name: Optional[str] = None, **read_kwargs: Any) -> dict[str, Any]:
        df = pd.read_csv(path, **read_kwargs)
        key = name or Path(path).stem
        self._frames[key] = df
        self._active = key
        return {"name": key, "rows": len(df), "columns": list(df.columns)}

    def preview(self, name: Optional[str] = None, n: int = 5) -> dict[str, Any]:
        df = self._get(name)
        return {
            "name": name or self._active,
            "columns": list(df.columns),
            "dtypes": {c: str(t) for c, t in df.dtypes.items()},
            "head": df.head(n).astype(object).where(pd.notnull(df.head(n)), None).to_dict(
                orient="records"
            ),
            "rows": len(df),
        }

    def rename_columns(self, mapping: dict[str, str], name: Optional[str] = None) -> dict[str, Any]:
        df = self._get(name)
        df.rename(columns=mapping, inplace=True)
        return {"name": name or self._active, "columns": list(df.columns)}

    def cast_types(self, mapping: dict[str, str], name: Optional[str] = None) -> dict[str, Any]:
        df = self._get(name)
        for col, dtype in mapping.items():
            if col not in df.columns:
                continue
            if dtype.lower() in {"datetime", "date", "timestamp"}:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            else:
                df[col] = df[col].astype(dtype)
        return {
            "name": name or self._active,
            "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        }

    def filter_rows(self, query: str, name: Optional[str] = None) -> dict[str, Any]:
        df = self._get(name)
        filtered = df.query(query)
        key = name or self._active
        assert key is not None
        self._frames[key] = filtered
        return {"name": key, "rows": len(filtered)}

    def write_table(
        self,
        table_name: str,
        name: Optional[str] = None,
        *,
        if_exists: str = "replace",
    ) -> dict[str, Any]:
        df = self._get(name)
        df.to_sql(table_name, self.engine, if_exists=if_exists, index=False)
        return {"table": table_name, "rows": len(df)}

    def _get(self, name: Optional[str] = None) -> pd.DataFrame:
        key = name or self._active
        if not key or key not in self._frames:
            raise ValueError("No dataframe loaded. Call load_csv first.")
        return self._frames[key]
