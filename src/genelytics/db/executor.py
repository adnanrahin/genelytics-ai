from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine


# Analytics-mode allowlist prefixes
_READ_ONLY_PREFIXES = (
    "SELECT",
    "WITH",
    "SHOW",
    "DESCRIBE",
    "DESC",
    "EXPLAIN",
    "PRAGMA",
)

_DANGEROUS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|REPLACE|GRANT|REVOKE|"
    r"ATTACH|DETACH|COPY|CALL|EXEC|EXECUTE|INTO\s+OUTFILE|LOAD\s+DATA)\b",
    re.IGNORECASE,
)


class SQLSafetyError(ValueError):
    """Raised when SQL is blocked by analytics safety rules."""


@dataclass
class QueryResult:
    columns: list[str] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    sql: str = ""


def strip_sql_fences(sql: str) -> str:
    """Remove markdown code fences and leading 'SQLQuery:' labels."""
    cleaned = (sql or "").strip()
    cleaned = re.sub(r"^```(?:sql)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = re.sub(r"^(SQLQuery|SQL|Query)\s*:\s*", "", cleaned, flags=re.IGNORECASE)
    # Often models emit explanation after the query — keep first statement
    if ";" in cleaned:
        parts = [p.strip() for p in cleaned.split(";") if p.strip()]
        if parts:
            cleaned = parts[0]
    return cleaned.strip().rstrip(";").strip()


def is_read_only_sql(sql: str) -> bool:
    normalized = strip_sql_fences(sql)
    if not normalized:
        return False
    upper = normalized.lstrip().upper()
    if not any(upper.startswith(prefix) for prefix in _READ_ONLY_PREFIXES):
        return False
    # Disallow stacked statements
    if ";" in normalized.rstrip(";"):
        return False
    # SELECT/WITH must not contain write verbs
    if upper.startswith(("SELECT", "WITH")) and _DANGEROUS.search(normalized):
        return False
    return True


def assert_safe_sql(sql: str, *, read_only: bool = True) -> str:
    cleaned = strip_sql_fences(sql)
    if not cleaned:
        raise SQLSafetyError("Empty SQL statement.")
    if read_only and not is_read_only_sql(cleaned):
        raise SQLSafetyError(
            "Only read-only statements (SELECT/WITH/SHOW/DESCRIBE/EXPLAIN) "
            "are allowed in analytics mode."
        )
    return cleaned


class QueryExecutor:
    """Run SQL with timeout, row limit, and optional read-only guard."""

    def __init__(
        self,
        engine: Engine,
        *,
        max_rows: int = 100,
        timeout_seconds: int = 30,
        read_only: bool = True,
    ) -> None:
        self.engine = engine
        self.max_rows = max_rows
        self.timeout_seconds = timeout_seconds
        self.read_only = read_only

    def run(self, sql: str, *, read_only: Optional[bool] = None) -> QueryResult:
        enforce = self.read_only if read_only is None else read_only
        cleaned = assert_safe_sql(sql, read_only=enforce)
        limit = self.max_rows

        # Soft-wrap SELECT without LIMIT when possible
        exec_sql = cleaned
        upper = cleaned.upper()
        if enforce and upper.startswith(("SELECT", "WITH")) and "LIMIT" not in upper:
            exec_sql = f"{cleaned} LIMIT {limit + 1}"

        connect_args: dict[str, Any] = {}
        # dialect-specific timeouts are best-effort; use execution_options where possible
        with self.engine.connect() as conn:
            if self.timeout_seconds:
                try:
                    conn = conn.execution_options(timeout=self.timeout_seconds)
                except Exception:
                    pass
            result = conn.execute(text(exec_sql))
            if result.returns_rows:
                keys = list(result.keys())
                fetched = result.fetchmany(limit + 1)
                truncated = len(fetched) > limit
                rows_raw = fetched[:limit]
                rows = [dict(zip(keys, row)) for row in rows_raw]
                # JSON-serialize friendly values
                rows = [_serialize_row(r) for r in rows]
                return QueryResult(
                    columns=keys,
                    rows=rows,
                    row_count=len(rows),
                    truncated=truncated,
                    sql=cleaned,
                )
            conn.commit()
            return QueryResult(columns=[], rows=[], row_count=result.rowcount or 0, sql=cleaned)


def _serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        elif isinstance(v, (bytes, bytearray)):
            out[k] = v.decode("utf-8", errors="replace")
        else:
            out[k] = v
    return out
