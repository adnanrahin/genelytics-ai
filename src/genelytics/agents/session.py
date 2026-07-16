from __future__ import annotations

from typing import Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


class SessionStore:
    """In-memory chat history keyed by session_id."""

    def __init__(self) -> None:
        self._sessions: dict[str, list[BaseMessage]] = {}

    def get(self, session_id: str) -> list[BaseMessage]:
        return list(self._sessions.get(session_id, []))

    def add_user(self, session_id: str, content: str) -> None:
        self._sessions.setdefault(session_id, []).append(HumanMessage(content=content))

    def add_ai(self, session_id: str, content: str) -> None:
        self._sessions.setdefault(session_id, []).append(AIMessage(content=content))

    def clear(self, session_id: Optional[str] = None) -> None:
        if session_id is None:
            self._sessions.clear()
        else:
            self._sessions.pop(session_id, None)

    def format_history(self, session_id: str, max_messages: int = 10) -> str:
        messages = self.get(session_id)[-max_messages:]
        lines: list[str] = []
        for msg in messages:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            lines.append(f"{role}: {msg.content}")
        return "\n".join(lines)
