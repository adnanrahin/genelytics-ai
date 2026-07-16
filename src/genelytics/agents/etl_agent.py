from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from genelytics.agents.session import SessionStore
from genelytics.etl.pipeline import PandasETLPipeline


@dataclass
class ETLAgentResult:
    answer: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    table: Optional[str] = None
    row_count: Optional[int] = None


_ETL_SYSTEM = """You are an ETL planner. Given a user request about loading/transforming data,
return a JSON object with a "steps" array. Each step has "tool" and "args".

Available tools:
- load_csv: args {path, name?}
- preview: args {name?, n?}
- rename_columns: args {mapping: {old: new}, name?}
- cast_types: args {mapping: {col: dtype}, name?}  dtype may be datetime/int/float/str
- filter_rows: args {query: pandas query string, name?}
- write_table: args {table_name, name?, if_exists?}

Return ONLY valid JSON, no markdown.
Example:
{"steps":[{"tool":"load_csv","args":{"path":"./sales.csv"}},{"tool":"write_table","args":{"table_name":"monthly_sales"}}]}
"""


class ETLAgent:
    """Chat-driven pandas ETL via planned tool steps."""

    def __init__(
        self,
        llm: Any,
        pipeline: PandasETLPipeline,
        sessions: Optional[SessionStore] = None,
    ) -> None:
        self.llm = llm
        self.pipeline = pipeline
        self.sessions = sessions or SessionStore()

    def run(self, instruction: str, *, session_id: str = "default") -> ETLAgentResult:
        try:
            steps = self._plan(instruction)
            executed: list[dict[str, Any]] = []
            last: dict[str, Any] = {}
            for step in steps:
                tool = step.get("tool")
                args = step.get("args") or {}
                last = self._dispatch(tool, args)
                executed.append({"tool": tool, "args": args, "result": last})

            table = last.get("table")
            rows = last.get("rows")
            answer = self._summarize(instruction, executed, last)
            self.sessions.add_user(session_id, instruction)
            self.sessions.add_ai(session_id, answer)
            return ETLAgentResult(
                answer=answer,
                steps=executed,
                table=table,
                row_count=rows,
            )
        except Exception as exc:  # noqa: BLE001
            return ETLAgentResult(answer="", error=str(exc))

    def _plan(self, instruction: str) -> list[dict[str, Any]]:
        messages = [
            SystemMessage(content=_ETL_SYSTEM),
            HumanMessage(content=instruction),
        ]
        response = self.llm.invoke(messages)
        content = getattr(response, "content", response)
        text = str(content).strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)
        steps = data.get("steps") if isinstance(data, dict) else data
        if not isinstance(steps, list) or not steps:
            raise ValueError("ETL planner returned no steps.")
        return steps

    def _dispatch(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        if tool == "load_csv":
            return self.pipeline.load_csv(**args)
        if tool == "preview":
            return self.pipeline.preview(**args)
        if tool == "rename_columns":
            return self.pipeline.rename_columns(**args)
        if tool == "cast_types":
            return self.pipeline.cast_types(**args)
        if tool == "filter_rows":
            return self.pipeline.filter_rows(**args)
        if tool == "write_table":
            return self.pipeline.write_table(**args)
        raise ValueError(f"Unknown ETL tool: {tool}")

    def _summarize(
        self,
        instruction: str,
        executed: list[dict[str, Any]],
        last: dict[str, Any],
    ) -> str:
        table = last.get("table")
        rows = last.get("rows")
        if table is not None:
            return (
                f"ETL complete. Wrote {rows} rows into table '{table}'. "
                f"Executed {len(executed)} step(s)."
            )
        return f"ETL steps finished ({len(executed)}). Last result: {last}"
