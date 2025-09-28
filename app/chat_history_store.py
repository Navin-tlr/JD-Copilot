from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _iso_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _coerce_iso(value: str | datetime | None) -> str:
    if value is None:
        return _iso_now()
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat() + ("Z" if value.tzinfo is None else "")
    value = value.strip()
    if not value:
        return _iso_now()
    try:
        # Accept timestamps that already include timezone
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value if value.endswith("Z") or "+" in value else value + "Z"
    except ValueError:
        return _iso_now()


STOP_WORDS = {
    "the", "and", "for", "with", "about", "that", "from", "this", "those", "these",
    "what", "when", "where", "which", "who", "how", "many", "are", "can", "you",
    "give", "show", "tell", "more", "info", "details", "please", "could", "would",
    "into", "over", "into", "help", "need", "want", "looking", "into", "provide",
}


@dataclass
class SessionRecord:
    session_id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    last_message_preview: Optional[str]
    summary: Optional[str]


class ChatHistoryStore:
    """SQLite-backed store for chat transcripts and metadata."""

    def __init__(self, db_path: str = "data/chat_history.db") -> None:
        self.db_path = Path(db_path)
        _ensure_parent(self.db_path)
        self._ensure_schema()

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def ensure_session(self, user_id: str, session_id: str) -> None:
        """Ensure a session row exists for the given user."""
        now = _iso_now()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_sessions (session_id, user_id, title, created_at, updated_at, message_count, last_message_preview, summary, transcript)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO NOTHING
                """,
                (
                    session_id,
                    user_id,
                    "New Conversation",
                    now,
                    now,
                    0,
                    None,
                    None,
                    json.dumps([], ensure_ascii=False),
                ),
            )

    def sync_session(self, user_id: str, session_id: str, messages: List[Dict[str, Any]]) -> None:
        """Persist the full transcript and metadata for a session."""
        self.ensure_session(user_id, session_id)

        if not messages:
            return

        created_at = _coerce_iso(self._first_timestamp(messages))
        updated_at = _coerce_iso(self._last_timestamp(messages))
        message_count = len(messages)
        title = self._generate_title(messages)
        summary = self._build_summary(messages)
        last_preview = self._build_last_preview(messages)
        transcript_json = json.dumps(messages, ensure_ascii=False)

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE chat_sessions
                SET user_id = ?,
                    title = ?,
                    created_at = COALESCE(created_at, ?),
                    updated_at = ?,
                    message_count = ?,
                    last_message_preview = ?,
                    summary = ?,
                    transcript = ?
                WHERE session_id = ?
                """,
                (
                    user_id,
                    title,
                    created_at,
                    updated_at,
                    message_count,
                    last_preview,
                    summary,
                    transcript_json,
                    session_id,
                ),
            )

    def list_sessions(self, user_id: str) -> List[SessionRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT session_id, user_id, title, created_at, updated_at, message_count, last_message_preview, summary
                FROM chat_sessions
                WHERE user_id = ?
                ORDER BY updated_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [SessionRecord(**dict(row)) for row in rows]

    def get_transcript(self, user_id: str, session_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT transcript
                FROM chat_sessions
                WHERE session_id = ? AND user_id = ?
                """,
                (session_id, user_id),
            ).fetchone()
        if not row:
            return []
        try:
            data = row[0]
            if not data:
                return []
            parsed = json.loads(data)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        return []

    def delete_session(self, user_id: str, session_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM chat_sessions WHERE session_id = ? AND user_id = ?",
                (session_id, user_id),
            )
            return cur.rowcount > 0

    def delete_all_sessions(self, user_id: str) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM chat_sessions WHERE user_id = ?",
                (user_id,),
            )
            return cur.rowcount

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    message_count INTEGER NOT NULL DEFAULT 0,
                    last_message_preview TEXT,
                    summary TEXT,
                    transcript TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_updated
                ON chat_sessions(user_id, updated_at DESC);
                """
            )

    @staticmethod
    def _first_timestamp(messages: List[Dict[str, Any]]) -> Optional[str]:
        if not messages:
            return None
        ts = messages[0].get("timestamp")
        return ts or None

    @staticmethod
    def _last_timestamp(messages: List[Dict[str, Any]]) -> Optional[str]:
        if not messages:
            return None
        ts = messages[-1].get("timestamp")
        return ts or None

    def _generate_title(self, messages: List[Dict[str, Any]]) -> str:
        user_messages = [m for m in messages if (m.get("role") == "user" and m.get("content"))]
        if not user_messages:
            return "Conversation"

        seed = user_messages[0]["content"].strip()
        if seed:
            clean = self._normalize_sentence(seed)
            if clean:
                return clean

        # Fallback: build from keywords across first few user turns
        corpus = " ".join(m.get("content", "") for m in user_messages[:3])
        keywords = self._extract_keywords(corpus)
        if keywords:
            if len(keywords) >= 2:
                return f"{keywords[0].title()} & {keywords[1].title()}"
            return keywords[0].title()

        return "Conversation"

    def _build_summary(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        if not messages:
            return None

        user_questions = [self._normalize_clause(m.get("content", "")) for m in messages if m.get("role") == "user"]
        assistant_responses = [self._normalize_clause(m.get("content", "")) for m in messages if m.get("role") == "assistant"]

        summary_parts: List[str] = []
        if user_questions:
            summary_parts.append(f"User topics: {', '.join(user_questions[:2])}")
        if assistant_responses:
            summary_parts.append(f"Latest answer: {assistant_responses[-1]}")
        return "; ".join(summary_parts) if summary_parts else None

    @staticmethod
    def _build_last_preview(messages: List[Dict[str, Any]]) -> Optional[str]:
        if not messages:
            return None
        preview = messages[-1].get("content") or ""
        preview = preview.strip()
        if len(preview) > 160:
            preview = preview[:157] + "..."
        return preview or None

    @staticmethod
    def _normalize_sentence(text: str) -> Optional[str]:
        if not text:
            return None
        text = text.strip()
        if not text:
            return None
        # Take the first sentence up to punctuation
        for sep in ["?", "!", ".", "\n"]:
            if sep in text:
                text = text.split(sep, 1)[0]
                break
        text = text.strip()
        if not text:
            return None
        if len(text) > 64:
            text = text[:61].rstrip() + "..."
        return text[0].upper() + text[1:] if text else None

    def _extract_keywords(self, text: str) -> List[str]:
        if not text:
            return []
        words: Dict[str, int] = {}
        for raw in text.replace("\n", " ").split():
            token = ''.join(ch for ch in raw if ch.isalnum()).lower()
            if len(token) < 3 or token in STOP_WORDS:
                continue
            words[token] = words.get(token, 0) + 1
        # Sort by frequency then alphabetically
        ranked = sorted(words.items(), key=lambda item: (-item[1], item[0]))
        return [w for w, _ in ranked[:4]]

    @staticmethod
    def _normalize_clause(text: str) -> str:
        if not text:
            return ""
        text = text.strip()
        if len(text) > 80:
            text = text[:77].rstrip() + "..."
        return text


# Global singleton used across the app
chat_history_store = ChatHistoryStore()
