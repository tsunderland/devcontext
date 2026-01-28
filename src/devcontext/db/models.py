"""Database models for DevContext."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Project:
    """A tracked project."""
    id: Optional[int] = None
    name: str = ""
    path: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_row(cls, row: tuple) -> "Project":
        """Create Project from database row."""
        return cls(
            id=row[0],
            name=row[1],
            path=row[2],
            created_at=datetime.fromisoformat(row[3]),
            last_active=datetime.fromisoformat(row[4]),
        )


@dataclass
class Session:
    """A work session on a project."""
    id: Optional[int] = None
    project_id: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    summary: Optional[str] = None

    @classmethod
    def from_row(cls, row: tuple) -> "Session":
        """Create Session from database row."""
        return cls(
            id=row[0],
            project_id=row[1],
            started_at=datetime.fromisoformat(row[2]),
            ended_at=datetime.fromisoformat(row[3]) if row[3] else None,
            summary=row[4],
        )

    @property
    def is_active(self) -> bool:
        """Check if session is still active."""
        return self.ended_at is None


@dataclass
class Capture:
    """A captured piece of context."""
    id: Optional[int] = None
    session_id: int = 0
    capture_type: str = ""  # git_commit, git_diff, file_change, terminal
    content: str = ""
    metadata: str = ""  # JSON string for extra data
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_row(cls, row: tuple) -> "Capture":
        """Create Capture from database row."""
        return cls(
            id=row[0],
            session_id=row[1],
            capture_type=row[2],
            content=row[3],
            metadata=row[4],
            timestamp=datetime.fromisoformat(row[5]),
        )


@dataclass
class Note:
    """A user-added note."""
    id: Optional[int] = None
    session_id: int = 0
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def from_row(cls, row: tuple) -> "Note":
        """Create Note from database row."""
        return cls(
            id=row[0],
            session_id=row[1],
            content=row[2],
            timestamp=datetime.fromisoformat(row[3]),
        )
