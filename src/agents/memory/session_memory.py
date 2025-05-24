from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..items import TResponseInputItem


@runtime_checkable
class SessionMemory(Protocol):
    """Protocol for session memory implementations.

    Session memory stores conversation history across agent runs, allowing
    agents to maintain context without requiring explicit manual memory management.
    """

    async def get_messages(self, session_id: str) -> list[TResponseInputItem]:
        """Retrieve the conversation history for a given session.

        Args:
            session_id: Unique identifier for the conversation session

        Returns:
            List of input items representing the conversation history
        """
        ...

    async def add_messages(
        self, session_id: str, messages: list[TResponseInputItem]
    ) -> None:
        """Add new messages to the conversation history.

        Args:
            session_id: Unique identifier for the conversation session
            messages: List of input items to add to the history
        """
        ...

    async def clear_session(self, session_id: str) -> None:
        """Clear all messages for a given session.

        Args:
            session_id: Unique identifier for the conversation session
        """
        ...


class SQLiteSessionMemory(SessionMemory):
    """SQLite-based implementation of session memory.

    This implementation stores conversation history in a SQLite database.
    By default, uses an in-memory database that is lost when the process ends.
    For persistent storage, provide a file path.
    """

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        sessions_table: str = "agent_sessions",
        messages_table: str = "agent_messages",
    ):
        """Initialize the SQLite session memory.

        Args:
            db_path: Path to the SQLite database file. Defaults to ':memory:' (in-memory database)
            sessions_table: Name of the table to store session metadata. Defaults to 'agent_sessions'
            messages_table: Name of the table to store message data. Defaults to 'agent_messages'
        """
        self.db_path = db_path
        self.sessions_table = sessions_table
        self.messages_table = messages_table
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
            f"""
            CREATE TABLE IF NOT EXISTS {self.sessions_table} (
                session_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.messages_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                message_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES {self.sessions_table} (session_id) ON DELETE CASCADE
            )
        """
        )

        conn.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{self.messages_table}_session_id 
            ON {self.messages_table} (session_id, created_at)
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
            f"""
            SELECT message_data FROM {self.messages_table} 
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
            f"""
            INSERT OR IGNORE INTO {self.sessions_table} (session_id) VALUES (?)
        """,
            (session_id,),
        )

        # Add messages
        message_data = [(session_id, json.dumps(message)) for message in messages]
        conn.executemany(
            f"""
            INSERT INTO {self.messages_table} (session_id, message_data) VALUES (?, ?)
        """,
            message_data,
        )

        # Update session timestamp
        conn.execute(
            f"""
            UPDATE {self.sessions_table} SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?
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
        conn.execute(
            f"DELETE FROM {self.messages_table} WHERE session_id = ?", (session_id,)
        )
        conn.execute(
            f"DELETE FROM {self.sessions_table} WHERE session_id = ?", (session_id,)
        )
        conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self._local, "connection"):
            self._local.connection.close()
