from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


_DIALECT_LABELS = {
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "sqlite": "SQLite",
    "sql": "SQL",
}


def dialect_label(dialect: str) -> str:
    return _DIALECT_LABELS.get(dialect.lower(), dialect)


def load_few_shot_examples(path: str | Path, limit: int = 5) -> list[dict[str, str]]:
    path = Path(path)
    if not path.is_file():
        # try relative to CWD parents
        for base in [Path.cwd(), Path.cwd().parent]:
            candidate = base / path
            if candidate.is_file():
                path = candidate
                break
        else:
            return []
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        return []
    examples: list[dict[str, str]] = []
    for item in data[:limit]:
        if isinstance(item, dict) and "input" in item and "query" in item:
            examples.append({"input": str(item["input"]), "query": str(item["query"])})
    return examples


def format_few_shot_block(examples: list[dict[str, str]]) -> str:
    if not examples:
        return ""
    parts = ["Here are example questions and SQL queries:"]
    for i, ex in enumerate(examples, 1):
        parts.append(f"Example {i}:\nQuestion: {ex['input']}\nSQL: {ex['query']}")
    return "\n\n".join(parts)


def build_sql_system_prompt(
    dialect: str,
    table_info: str,
    *,
    examples: Optional[list[dict[str, str]]] = None,
) -> str:
    label = dialect_label(dialect)
    few_shot = format_few_shot_block(examples or [])
    return (
        f"You are a {label} expert. Given an input question, create a syntactically "
        f"correct {label} query to run. Return ONLY the SQL query with no markdown "
        f"fences and no explanation.\n"
        f"Prefer aggregations and joins when needed. Use only columns that exist in "
        f"the schema. Unless the user asks for everything, limit results reasonably.\n\n"
        f"Relevant table info:\n{table_info}\n"
        + (f"\n{few_shot}\n" if few_shot else "")
    )


def build_answer_system_prompt() -> str:
    return (
        "You are a helpful data analyst. Given the user's question, the SQL that was "
        "run, and the query result rows, write a clear natural-language answer. "
        "Mention key numbers and trends. Be concise. If the result is empty, say so."
    )
