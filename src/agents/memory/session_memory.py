from __future__ import annotations

import abc
import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..items import TResponseInputItem


class SessionMemory(abc.ABC):
    """Abstract base class for session memory implementations.

    Session memory stores conversation history across agent runs, allowing
    agents to maintain context without requiring explicit manual memory management.
    """

    @abc.abstractmethod
    async def get_messages(self, session_id: str) -> list[TResponseInputItem]:
        """Retrieve the conversation history for a given session.

        Args:
            session_id: Unique identifier for the conversation session

        Returns:
            List of input items representing the conversation history
        """
        pass

    @abc.abstractmethod
    async def add_messages(
        self, session_id: str, messages: list[TResponseInputItem]
    ) -> None:
        """Add new messages to the conversation history.

        Args:
            session_id: Unique identifier for the conversation session
            messages: List of input items to add to the history
        """
        pass

    @abc.abstractmethod
    async def clear_session(self, session_id: str) -> None:
        """Clear all messages for a given session.

        Args:
            session_id: Unique identifier for the conversation session
        """
        pass


class SQLiteSessionMemory(SessionMemory):
    """SQLite-based implementation of session memory.

    This implementation stores conversation history in a SQLite database.
    By default, uses an in-memory database that is lost when the process ends.
    For persistent storage, provide a file path.
    """

    def __init__(self, db_path: str | Path = ":memory:"):
        """Initialize the SQLite session memory.

        Args:
            db_path: Path to the SQLite database file. Defaults to ':memory:' (in-memory database)
        """
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(
                str(self.db_path) if self.db_path != ":memory:" else self.db_path,
                check_same_thread=False,
            )
            self._local.connection.execute("PRAGMA journal_mode=WAL")
        return self._local.connection

    def _init_db(self) -> None:
        """Initialize the database schema."""
        conn = self._get_connection()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                message_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
            )
        """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_messages_session_id 
            ON messages (session_id, created_at)
        """
        )

        conn.commit()

    async def get_messages(self, session_id: str) -> list[TResponseInputItem]:
        """Retrieve the conversation history for a given session.

        Args:
            session_id: Unique identifier for the conversation session

        Returns:
            List of input items representing the conversation history
        """
        conn = self._get_connection()
        cursor = conn.execute(
            """
            SELECT message_data FROM messages 
            WHERE session_id = ? 
            ORDER BY created_at ASC
        """,
            (session_id,),
        )

        messages = []
        for (message_data,) in cursor.fetchall():
            try:
                message = json.loads(message_data)
                messages.append(message)
            except json.JSONDecodeError:
                # Skip invalid JSON entries
                continue

        return messages

    async def add_messages(
        self, session_id: str, messages: list[TResponseInputItem]
    ) -> None:
        """Add new messages to the conversation history.

        Args:
            session_id: Unique identifier for the conversation session
            messages: List of input items to add to the history
        """
        if not messages:
            return

        conn = self._get_connection()

        # Ensure session exists
        conn.execute(
            """
            INSERT OR IGNORE INTO sessions (session_id) VALUES (?)
        """,
            (session_id,),
        )

        # Add messages
        message_data = [(session_id, json.dumps(message)) for message in messages]
        conn.executemany(
            """
            INSERT INTO messages (session_id, message_data) VALUES (?, ?)
        """,
            message_data,
        )

        # Update session timestamp
        conn.execute(
            """
            UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?
        """,
            (session_id,),
        )

        conn.commit()

    async def clear_session(self, session_id: str) -> None:
        """Clear all messages for a given session.

        Args:
            session_id: Unique identifier for the conversation session
        """
        conn = self._get_connection()
        conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self._local, "connection"):
            self._local.connection.close()
