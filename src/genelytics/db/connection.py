from __future__ import annotations

from typing import Any, Optional
from urllib.parse import quote_plus

from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

# UI historically sent "postgres"; SQLAlchemy wants postgresql
_DIALECT_ALIASES = {
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "pg": "postgresql",
    "mysql": "mysql",
    "sqlite": "sqlite",
    "mariadb": "mysql",
}

_DRIVER_DEFAULTS = {
    "postgresql": "postgresql+psycopg2",
    "mysql": "mysql+pymysql",
    "sqlite": "sqlite",
}


def normalize_db_type(db_type: str) -> str:
    key = (db_type or "").strip().lower()
    if key not in _DIALECT_ALIASES:
        raise ValueError(
            f"Unsupported database type '{db_type}'. "
            "Use mysql, postgres/postgresql, or sqlite."
        )
    return _DIALECT_ALIASES[key]


def build_database_uri(
    *,
    uri: Optional[str] = None,
    db_type: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[str | int] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    database_schema: Optional[str] = None,
    database: Optional[str] = None,
    **_: Any,
) -> str:
    """Build a SQLAlchemy URI from a raw URI or structured kwargs."""
    if uri:
        return uri

    if not db_type:
        raise ValueError("Either 'uri' or 'db_type' is required.")

    dialect = normalize_db_type(db_type)
    db_name = database_schema or database

    if dialect == "sqlite":
        path = db_name or ":memory:"
        if path == ":memory:":
            return "sqlite:///:memory:"
        return f"sqlite:///{path}"

    scheme = _DRIVER_DEFAULTS[dialect]
    user = quote_plus(username or "")
    pwd = quote_plus(password or "")
    host = host or "localhost"
    port_part = f":{port}" if port else ""
    db_part = f"/{db_name}" if db_name else ""
    auth = f"{user}:{pwd}@" if (username or password) else ""
    return f"{scheme}://{auth}{host}{port_part}{db_part}"


def create_sqlalchemy_engine(uri: str, **engine_kwargs: Any) -> Engine:
    return create_engine(uri, pool_pre_ping=True, **engine_kwargs)


def create_sql_database(
    uri: str,
    *,
    sample_rows_in_table_info: int = 2,
    include_tables: Optional[list[str]] = None,
) -> SQLDatabase:
    engine = create_sqlalchemy_engine(uri)
    tables = include_tables
    if tables is None:
        try:
            tables = inspect(engine).get_table_names()
        except Exception:
            tables = None
    kwargs: dict[str, Any] = {"sample_rows_in_table_info": sample_rows_in_table_info}
    if tables:
        kwargs["include_tables"] = tables
    return SQLDatabase(engine, **kwargs)


def dialect_name_from_uri(uri: str) -> str:
    lowered = uri.lower()
    if lowered.startswith("mysql"):
        return "mysql"
    if lowered.startswith("postgres"):
        return "postgresql"
    if lowered.startswith("sqlite"):
        return "sqlite"
    return "sql"
