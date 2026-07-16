from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from langchain_community.utilities import SQLDatabase
from sqlalchemy.engine import Engine

from genelytics.agents.etl_agent import ETLAgent, ETLAgentResult
from genelytics.agents.router import Intent, classify_intent
from genelytics.agents.session import SessionStore
from genelytics.agents.sql_agent import SQLAgentResult, SQLAnalyticsAgent
from genelytics.config.loader import load_settings
from genelytics.config.settings import Settings
from genelytics.db.connection import (
    build_database_uri,
    create_sql_database,
    create_sqlalchemy_engine,
    dialect_name_from_uri,
)
from genelytics.db.executor import QueryExecutor
from genelytics.etl.pipeline import PandasETLPipeline
from genelytics.llm.factory import create_chat_model


@dataclass
class AskResult:
    answer: str = ""
    sql: Optional[str] = None
    data: list[dict[str, Any]] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    error: Optional[str] = None
    intent: Optional[str] = None
    truncated: bool = False
    # backward-compatible alias used by older UIs
    result: Optional[str] = None

    def __post_init__(self) -> None:
        if self.result is None:
            self.result = self.answer or self.error or ""


class AnalyticsEngine:
    """Public facade: connect → ask / etl."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.llm = create_chat_model(settings.llm)
        self.sessions = SessionStore()
        self._engine: Optional[Engine] = None
        self._sql_db: Optional[SQLDatabase] = None
        self._executor: Optional[QueryExecutor] = None
        self._uri: Optional[str] = None
        self._pipeline: Optional[PandasETLPipeline] = None

        if settings.database.uri:
            self.connect(uri=settings.database.uri)

    @classmethod
    def from_env(
        cls,
        env: Optional[str] = None,
        config_dir: Optional[str | Path] = None,
    ) -> "AnalyticsEngine":
        return cls(load_settings(env=env, config_dir=config_dir))

    @classmethod
    def from_yaml(cls, path: str | Path) -> "AnalyticsEngine":
        return cls(load_settings(yaml_path=path))

    @property
    def is_connected(self) -> bool:
        return self._engine is not None

    @property
    def uri(self) -> Optional[str]:
        return self._uri

    def connect(self, uri: Optional[str] = None, **kwargs: Any) -> "AnalyticsEngine":
        self._uri = build_database_uri(uri=uri, **kwargs) if (uri or kwargs) else None
        if not self._uri:
            raise ValueError("Provide a database uri or connection kwargs.")
        self._engine = create_sqlalchemy_engine(self._uri)
        self._sql_db = create_sql_database(self._uri)
        self._executor = QueryExecutor(
            self._engine,
            max_rows=self.settings.analytics.max_rows,
            timeout_seconds=self.settings.analytics.query_timeout_seconds,
            read_only=self.settings.analytics.read_only,
        )
        self._pipeline = PandasETLPipeline(self._engine)
        return self

    def ask(self, question: str, *, session_id: str = "default") -> AskResult:
        self._require_db()
        intent = classify_intent(question, llm=None)
        if intent is Intent.META:
            return self._meta(question, session_id=session_id)
        if intent is Intent.ETL:
            etl_result = self.etl(question, session_id=session_id)
            return AskResult(
                answer=etl_result.answer or etl_result.error or "",
                error=etl_result.error,
                intent=Intent.ETL.value,
            )

        assert self._sql_db is not None and self._executor is not None
        agent = SQLAnalyticsAgent(
            self.llm,
            self._sql_db,
            self._executor,
            self.settings,
            sessions=self.sessions,
            dialect=dialect_name_from_uri(self._uri or ""),
        )
        result: SQLAgentResult = agent.ask(question, session_id=session_id)
        return AskResult(
            answer=result.answer,
            sql=result.sql,
            data=result.data,
            columns=result.columns,
            error=result.error,
            intent=Intent.ANALYTICS.value,
            truncated=result.truncated,
        )

    def etl(self, instruction: str, *, session_id: str = "default") -> ETLAgentResult:
        self._require_db()
        assert self._pipeline is not None
        agent = ETLAgent(self.llm, self._pipeline, sessions=self.sessions)
        return agent.run(instruction, session_id=session_id)

    def list_tables(self) -> list[str]:
        self._require_db()
        assert self._sql_db is not None
        return list(self._sql_db.get_usable_table_names())

    def _meta(self, question: str, *, session_id: str) -> AskResult:
        assert self._sql_db is not None
        tables = self.list_tables()
        if re_describe(question):
            info = self._sql_db.get_table_info()
            answer = f"Schema overview:\n{info}"
        else:
            answer = "Tables:\n" + "\n".join(f"- {t}" for t in tables)
        self.sessions.add_user(session_id, question)
        self.sessions.add_ai(session_id, answer)
        return AskResult(answer=answer, intent=Intent.META.value, data=[{"tables": tables}])

    def _require_db(self) -> None:
        if not self.is_connected:
            raise RuntimeError("Database not connected. Call connect() first.")


def re_describe(text: str) -> bool:
    import re

    return bool(re.search(r"\b(describe|schema|columns?)\b", text, re.IGNORECASE))
