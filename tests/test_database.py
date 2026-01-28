"""Tests for database operations."""

import tempfile
from pathlib import Path

import pytest

from devcontext.db import Database, Project, Session


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield Database(db_path)


class TestProject:
    """Tests for project operations."""

    def test_create_project(self, db):
        """Test creating a new project."""
        project = db.create_project("test-project", "/path/to/project")

        assert project.id is not None
        assert project.name == "test-project"
        assert project.path == "/path/to/project"

    def test_get_project_by_path(self, db):
        """Test retrieving project by path."""
        db.create_project("test-project", "/path/to/project")

        project = db.get_project_by_path("/path/to/project")

        assert project is not None
        assert project.name == "test-project"

    def test_get_nonexistent_project(self, db):
        """Test retrieving non-existent project."""
        project = db.get_project_by_path("/nonexistent")

        assert project is None

    def test_list_projects(self, db):
        """Test listing all projects."""
        db.create_project("project1", "/path/1")
        db.create_project("project2", "/path/2")

        projects = db.list_projects()

        assert len(projects) == 2


class TestSession:
    """Tests for session operations."""

    def test_create_session(self, db):
        """Test creating a new session."""
        project = db.create_project("test", "/path")
        session = db.create_session(project.id)

        assert session.id is not None
        assert session.project_id == project.id
        assert session.is_active

    def test_end_session(self, db):
        """Test ending a session."""
        project = db.create_project("test", "/path")
        session = db.create_session(project.id)

        db.end_session(session.id, "Test summary")

        # Verify session is ended
        active = db.get_active_session(project.id)
        assert active is None

    def test_get_active_session(self, db):
        """Test getting active session."""
        project = db.create_project("test", "/path")

        # No active session initially
        assert db.get_active_session(project.id) is None

        # Create session
        session = db.create_session(project.id)
        active = db.get_active_session(project.id)

        assert active is not None
        assert active.id == session.id


class TestNotes:
    """Tests for note operations."""

    def test_add_note(self, db):
        """Test adding a note."""
        project = db.create_project("test", "/path")
        session = db.create_session(project.id)

        note = db.add_note(session.id, "Test note content")

        assert note.id is not None
        assert note.content == "Test note content"

    def test_get_session_notes(self, db):
        """Test getting notes for a session."""
        project = db.create_project("test", "/path")
        session = db.create_session(project.id)

        db.add_note(session.id, "Note 1")
        db.add_note(session.id, "Note 2")

        notes = db.get_session_notes(session.id)

        assert len(notes) == 2
