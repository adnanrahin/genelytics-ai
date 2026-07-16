from __future__ import annotations

import pytest
from sqlalchemy import create_engine, text

from genelytics.db.connection import build_database_uri, normalize_db_type
from genelytics.db.executor import (
    QueryExecutor,
    SQLSafetyError,
    assert_safe_sql,
    is_read_only_sql,
    strip_sql_fences,
)


def test_normalize_postgres_alias():
    assert normalize_db_type("postgres") == "postgresql"
    assert normalize_db_type("postgresql") == "postgresql"
    assert normalize_db_type("mysql") == "mysql"


def test_build_uri_postgres():
    uri = build_database_uri(
        db_type="postgres",
        host="localhost",
        port=5432,
        username="u",
        password="p",
        database_schema="db",
    )
    assert uri.startswith("postgresql+psycopg2://")
    assert "localhost:5432/db" in uri


def test_strip_fences():
    assert strip_sql_fences("```sql\nSELECT 1\n```") == "SELECT 1"
    assert strip_sql_fences("SQLQuery: SELECT 1;") == "SELECT 1"


def test_read_only_guard():
    assert is_read_only_sql("SELECT * FROM t")
    assert is_read_only_sql("WITH x AS (SELECT 1) SELECT * FROM x")
    assert not is_read_only_sql("DELETE FROM t")
    assert not is_read_only_sql("DROP TABLE t")
    with pytest.raises(SQLSafetyError):
        assert_safe_sql("UPDATE t SET a=1", read_only=True)


def test_executor_select_limit():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE items (id INTEGER, name TEXT)"))
        conn.execute(text("INSERT INTO items VALUES (1, 'a'), (2, 'b'), (3, 'c')"))
    ex = QueryExecutor(engine, max_rows=2, read_only=True)
    result = ex.run("SELECT * FROM items ORDER BY id")
    assert result.row_count == 2
    assert result.truncated is True
    assert result.rows[0]["name"] == "a"


def test_executor_blocks_write():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE items (id INTEGER)"))
    ex = QueryExecutor(engine, read_only=True)
    with pytest.raises(SQLSafetyError):
        ex.run("DELETE FROM items")
