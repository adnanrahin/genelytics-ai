from __future__ import annotations

import os

import pytest
import urllib.request

from genelytics.engine import AnalyticsEngine
from genelytics.db.connection import build_database_uri
from sqlalchemy import create_engine, text


def _ollama_up() -> bool:
    base = os.environ.get("GENELYTICS_LLM__BASE_URL", "http://127.0.0.1:11434")
    try:
        with urllib.request.urlopen(f"{base.rstrip('/')}/api/tags", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _ollama_up(), reason="Ollama not reachable")


def test_engine_ask_sqlite_smoke(tmp_path):
    db_path = tmp_path / "smoke.db"
    uri = f"sqlite:///{db_path}"
    engine = create_engine(uri)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE sales (id INTEGER, amount REAL)"))
        conn.execute(text("INSERT INTO sales VALUES (1, 10.5), (2, 20.0)"))

    eng = AnalyticsEngine.from_env()
    eng.connect(uri=uri)
    result = eng.ask("What is the total of amount in sales?")
    assert result.error is None or result.answer
    # At minimum we should get either SQL or a clear answer (not None from old bug)
    assert result.result is not None
    assert result.sql is not None or result.answer or result.error
