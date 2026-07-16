from __future__ import annotations

import re
from enum import Enum
from typing import Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage


class Intent(str, Enum):
    ANALYTICS = "analytics"
    ETL = "etl"
    META = "meta"


_ETL_KEYWORDS = re.compile(
    r"\b(load|etl|csv|ingest|import|normalize|transform|write\s+table|"
    r"rename\s+columns?|cast\s+types?|filter\s+rows?)\b",
    re.IGNORECASE,
)
_META_KEYWORDS = re.compile(
    r"\b(list\s+tables?|show\s+tables?|describe\s+(schema|database|table)|"
    r"what\s+tables?|schema\s+info|table\s+info)\b",
    re.IGNORECASE,
)


def classify_intent(text: str, llm: Any = None) -> Intent:
    """Keyword-first intent classification; optional LLM fallback."""
    if _ETL_KEYWORDS.search(text):
        return Intent.ETL
    if _META_KEYWORDS.search(text):
        return Intent.META
    if llm is None:
        return Intent.ANALYTICS
    try:
        messages = [
            SystemMessage(
                content=(
                    "Classify the user message as one of: analytics, etl, meta. "
                    "Return only the label."
                )
            ),
            HumanMessage(content=text),
        ]
        response = llm.invoke(messages)
        label = str(getattr(response, "content", response)).strip().lower()
        if "etl" in label:
            return Intent.ETL
        if "meta" in label:
            return Intent.META
    except Exception:
        pass
    return Intent.ANALYTICS
