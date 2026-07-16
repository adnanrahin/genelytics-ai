from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.utilities import SQLDatabase

from genelytics.agents.session import SessionStore
from genelytics.config.settings import Settings
from genelytics.db.connection import dialect_name_from_uri
from genelytics.db.executor import QueryExecutor, QueryResult, SQLSafetyError, strip_sql_fences
from genelytics.prompts.sql_system import (
    build_answer_system_prompt,
    build_sql_system_prompt,
    load_few_shot_examples,
)


@dataclass
class SQLAgentResult:
    answer: str
    sql: Optional[str] = None
    data: list[dict[str, Any]] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    error: Optional[str] = None
    truncated: bool = False


class SQLAnalyticsAgent:
    """NL → SQL → execute → natural-language answer."""

    def __init__(
        self,
        llm: Any,
        sql_database: SQLDatabase,
        executor: QueryExecutor,
        settings: Settings,
        sessions: Optional[SessionStore] = None,
        dialect: Optional[str] = None,
    ) -> None:
        self.llm = llm
        self.db = sql_database
        self.executor = executor
        self.settings = settings
        self.sessions = sessions or SessionStore()
        self.dialect = dialect or _infer_dialect(sql_database)

    def ask(self, question: str, *, session_id: str = "default") -> SQLAgentResult:
        history = self.sessions.format_history(session_id)
        try:
            sql = self._generate_sql(question, history=history)
            sql = strip_sql_fences(sql)
            result = self.executor.run(sql, read_only=True)
            answer = self._answer(question, sql, result)
            self.sessions.add_user(session_id, question)
            self.sessions.add_ai(
                session_id,
                f"SQL: {sql}\nAnswer: {answer}",
            )
            return SQLAgentResult(
                answer=answer,
                sql=sql,
                data=result.rows,
                columns=result.columns,
                truncated=result.truncated,
            )
        except SQLSafetyError as exc:
            return SQLAgentResult(answer="", error=str(exc))
        except Exception as exc:  # noqa: BLE001 — surface to callers
            return SQLAgentResult(answer="", error=str(exc))

    def _generate_sql(self, question: str, *, history: str) -> str:
        examples: list[dict[str, str]] = []
        if self.settings.few_shot.enabled:
            examples = load_few_shot_examples(
                self.settings.few_shot.path,
                limit=self.settings.few_shot.max_examples,
            )
        table_info = self.db.get_table_info()
        system = build_sql_system_prompt(self.dialect, table_info, examples=examples)
        if history:
            system += f"\n\nPrior conversation (for follow-ups):\n{history}"
        messages = [
            SystemMessage(content=system),
            HumanMessage(content=question),
        ]
        response = self.llm.invoke(messages)
        content = _message_content(response)
        return content

    def _answer(self, question: str, sql: str, result: QueryResult) -> str:
        preview = result.rows[: min(20, len(result.rows))]
        payload = (
            f"Question: {question}\n"
            f"SQL: {sql}\n"
            f"Columns: {result.columns}\n"
            f"Rows ({result.row_count}"
            f"{', truncated' if result.truncated else ''}): {preview}"
        )
        messages = [
            SystemMessage(content=build_answer_system_prompt()),
            HumanMessage(content=payload),
        ]
        response = self.llm.invoke(messages)
        return _message_content(response)


def _message_content(response: Any) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
            else:
                parts.append(str(block))
        return "\n".join(parts).strip()
    return str(content).strip()


def _infer_dialect(db: SQLDatabase) -> str:
    try:
        name = db.dialect
        if callable(name):
            name = name()
        return str(name).lower()
    except Exception:
        uri = str(getattr(db, "_engine", "") or "")
        if hasattr(db, "engine"):
            uri = str(db.engine.url)
        return dialect_name_from_uri(uri)
