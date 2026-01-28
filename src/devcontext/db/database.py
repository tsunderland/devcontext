"""Database operations for DevContext."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional

from ..config import DB_FILE, ensure_dirs
from .models import Capture, Note, Project, Session


class Database:
    """SQLite database manager for DevContext."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection."""
        self.db_path = db_path or DB_FILE
        ensure_dirs()
        self._init_schema()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self._connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    path TEXT UNIQUE NOT NULL,
                    created_at TEXT NOT NULL,
                    last_active TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    summary TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                );

                CREATE TABLE IF NOT EXISTS captures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    capture_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                );

                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id);
                CREATE INDEX IF NOT EXISTS idx_captures_session ON captures(session_id);
                CREATE INDEX IF NOT EXISTS idx_notes_session ON notes(session_id);
            """)

    # Project operations

    def create_project(self, name: str, path: str) -> Project:
        """Create a new project."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            cursor = conn.execute(
                "INSERT INTO projects (name, path, created_at, last_active) VALUES (?, ?, ?, ?)",
                (name, path, now, now)
            )
            return Project(
                id=cursor.lastrowid,
                name=name,
                path=path,
                created_at=datetime.fromisoformat(now),
                last_active=datetime.fromisoformat(now),
            )

    def get_project_by_path(self, path: str) -> Optional[Project]:
        """Get project by path."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id, name, path, created_at, last_active FROM projects WHERE path = ?",
                (path,)
            ).fetchone()
            return Project.from_row(tuple(row)) if row else None

    def get_project(self, project_id: int) -> Optional[Project]:
        """Get project by ID."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id, name, path, created_at, last_active FROM projects WHERE id = ?",
                (project_id,)
            ).fetchone()
            return Project.from_row(tuple(row)) if row else None

    def list_projects(self) -> list[Project]:
        """List all tracked projects."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT id, name, path, created_at, last_active FROM projects ORDER BY last_active DESC"
            ).fetchall()
            return [Project.from_row(tuple(row)) for row in rows]

    def update_project_activity(self, project_id: int) -> None:
        """Update project's last active timestamp."""
        with self._connection() as conn:
            conn.execute(
                "UPDATE projects SET last_active = ? WHERE id = ?",
                (datetime.now().isoformat(), project_id)
            )

    # Session operations

    def create_session(self, project_id: int) -> Session:
        """Create a new session."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            cursor = conn.execute(
                "INSERT INTO sessions (project_id, started_at) VALUES (?, ?)",
                (project_id, now)
            )
            # Update project activity in same transaction to avoid lock
            conn.execute(
                "UPDATE projects SET last_active = ? WHERE id = ?",
                (now, project_id)
            )
            return Session(
                id=cursor.lastrowid,
                project_id=project_id,
                started_at=datetime.fromisoformat(now),
            )

    def get_active_session(self, project_id: int) -> Optional[Session]:
        """Get active session for a project."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id, project_id, started_at, ended_at, summary "
                "FROM sessions WHERE project_id = ? AND ended_at IS NULL",
                (project_id,)
            ).fetchone()
            return Session.from_row(tuple(row)) if row else None

    def end_session(self, session_id: int, summary: Optional[str] = None) -> None:
        """End a session."""
        with self._connection() as conn:
            conn.execute(
                "UPDATE sessions SET ended_at = ?, summary = ? WHERE id = ?",
                (datetime.now().isoformat(), summary, session_id)
            )

    def get_recent_sessions(self, project_id: int, limit: int = 5) -> list[Session]:
        """Get recent sessions for a project."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT id, project_id, started_at, ended_at, summary "
                "FROM sessions WHERE project_id = ? ORDER BY started_at DESC LIMIT ?",
                (project_id, limit)
            ).fetchall()
            return [Session.from_row(tuple(row)) for row in rows]

    def get_last_session(self, project_id: int) -> Optional[Session]:
        """Get most recent completed session for a project."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT id, project_id, started_at, ended_at, summary "
                "FROM sessions WHERE project_id = ? AND ended_at IS NOT NULL "
                "ORDER BY ended_at DESC LIMIT 1",
                (project_id,)
            ).fetchone()
            return Session.from_row(tuple(row)) if row else None

    # Capture operations

    def add_capture(
        self,
        session_id: int,
        capture_type: str,
        content: str,
        metadata: str = "{}"
    ) -> Capture:
        """Add a context capture."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            cursor = conn.execute(
                "INSERT INTO captures (session_id, capture_type, content, metadata, timestamp) "
                "VALUES (?, ?, ?, ?, ?)",
                (session_id, capture_type, content, metadata, now)
            )
            return Capture(
                id=cursor.lastrowid,
                session_id=session_id,
                capture_type=capture_type,
                content=content,
                metadata=metadata,
                timestamp=datetime.fromisoformat(now),
            )

    def get_session_captures(self, session_id: int) -> list[Capture]:
        """Get all captures for a session."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT id, session_id, capture_type, content, metadata, timestamp "
                "FROM captures WHERE session_id = ? ORDER BY timestamp",
                (session_id,)
            ).fetchall()
            return [Capture.from_row(tuple(row)) for row in rows]

    # Note operations

    def add_note(self, session_id: int, content: str) -> Note:
        """Add a note to a session."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            cursor = conn.execute(
                "INSERT INTO notes (session_id, content, timestamp) VALUES (?, ?, ?)",
                (session_id, content, now)
            )
            return Note(
                id=cursor.lastrowid,
                session_id=session_id,
                content=content,
                timestamp=datetime.fromisoformat(now),
            )

    def get_session_notes(self, session_id: int) -> list[Note]:
        """Get all notes for a session."""
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT id, session_id, content, timestamp FROM notes WHERE session_id = ? ORDER BY timestamp",
                (session_id,)
            ).fetchall()
            return [Note.from_row(tuple(row)) for row in rows]

    def get_recent_notes(self, project_id: int, limit: int = 10) -> list[Note]:
        """Get recent notes across sessions for a project."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT n.id, n.session_id, n.content, n.timestamp
                FROM notes n
                JOIN sessions s ON n.session_id = s.id
                WHERE s.project_id = ?
                ORDER BY n.timestamp DESC
                LIMIT ?
                """,
                (project_id, limit)
            ).fetchall()
            return [Note.from_row(tuple(row)) for row in rows]
