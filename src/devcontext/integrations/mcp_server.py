"""MCP Server for DevContext - enables AI tools to manage context.

This allows AI coding assistants (Claude Code, etc.) to:
- Start/end sessions
- Add notes
- Get summaries
- Check project status

Run with: devctx mcp-serve
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from ..db import Database
from ..capture import GitCapture
from ..summary import OllamaSummarizer
from ..utils import format_time_ago, format_duration


def find_project_root(db: Database, start_path: Path):
    """Find project root by walking up directory tree."""
    current = start_path.resolve()
    project = db.get_project_by_path(str(current))
    if project:
        return project
    for parent in current.parents:
        project = db.get_project_by_path(str(parent))
        if project:
            return project
    return None


class DevContextMCPServer:
    """MCP Server implementation for DevContext."""

    def __init__(self):
        self.db = Database()

    def get_tools(self) -> list[dict]:
        """Return list of available MCP tools."""
        return [
            {
                "name": "devcontext_status",
                "description": "Get current project and session status",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Project path (defaults to cwd)"
                        }
                    }
                }
            },
            {
                "name": "devcontext_start",
                "description": "Start a new work session for context tracking",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Project path (defaults to cwd)"
                        }
                    }
                }
            },
            {
                "name": "devcontext_end",
                "description": "End current session and generate summary",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Project path (defaults to cwd)"
                        }
                    }
                }
            },
            {
                "name": "devcontext_note",
                "description": "Add a note to the current session",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "note": {
                            "type": "string",
                            "description": "Note content to add"
                        },
                        "path": {
                            "type": "string",
                            "description": "Project path (defaults to cwd)"
                        }
                    },
                    "required": ["note"]
                }
            },
            {
                "name": "devcontext_summary",
                "description": "Get AI summary of current session without ending it",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Project path (defaults to cwd)"
                        }
                    }
                }
            },
            {
                "name": "devcontext_resume",
                "description": "Get context to resume work on a project",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Project path (defaults to cwd)"
                        }
                    }
                }
            },
            {
                "name": "devcontext_init",
                "description": "Initialize DevContext tracking for a project",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Project path (defaults to cwd)"
                        },
                        "name": {
                            "type": "string",
                            "description": "Project name (defaults to directory name)"
                        }
                    }
                }
            }
        ]

    def call_tool(self, name: str, arguments: dict) -> dict:
        """Execute a tool and return result."""
        path = Path(arguments.get("path", ".")).resolve()

        handlers = {
            "devcontext_status": self._handle_status,
            "devcontext_start": self._handle_start,
            "devcontext_end": self._handle_end,
            "devcontext_note": self._handle_note,
            "devcontext_summary": self._handle_summary,
            "devcontext_resume": self._handle_resume,
            "devcontext_init": self._handle_init,
        }

        handler = handlers.get(name)
        if not handler:
            return {"error": f"Unknown tool: {name}"}

        try:
            return handler(path, arguments)
        except Exception as e:
            return {"error": str(e)}

    def _handle_status(self, path: Path, args: dict) -> dict:
        """Get project and session status."""
        project = find_project_root(self.db, path)
        if not project:
            return {"tracked": False, "message": "Project not initialized"}

        session = self.db.get_active_session(project.id)
        return {
            "tracked": True,
            "project": project.name,
            "path": project.path,
            "last_active": format_time_ago(project.last_active),
            "session_active": session is not None,
            "session_duration": format_duration(session.started_at, datetime.now()) if session else None
        }

    def _handle_start(self, path: Path, args: dict) -> dict:
        """Start a new session."""
        project = find_project_root(self.db, path)
        if not project:
            return {"success": False, "error": "Project not initialized. Run devctx init first."}

        existing = self.db.get_active_session(project.id)
        if existing:
            return {
                "success": True,
                "message": "Session already active",
                "duration": format_duration(existing.started_at, datetime.now())
            }

        session = self.db.create_session(project.id)

        # Capture git state
        git = GitCapture(Path(project.path))
        if git.is_git_repo():
            context = git.capture()
            if context:
                self.db.add_capture(session.id, "git_start", context.to_summary(), context.to_json())

        return {
            "success": True,
            "message": f"Session started for {project.name}",
            "session_id": session.id
        }

    def _handle_end(self, path: Path, args: dict) -> dict:
        """End current session."""
        project = find_project_root(self.db, path)
        if not project:
            return {"success": False, "error": "Project not initialized"}

        session = self.db.get_active_session(project.id)
        if not session:
            return {"success": False, "error": "No active session"}

        # Capture final state and generate summary
        git = GitCapture(Path(project.path))
        notes = [n.content for n in self.db.get_session_notes(session.id)]
        captures = [c.content for c in self.db.get_session_captures(session.id)]
        git_context = ""

        if git.is_git_repo():
            ctx = git.capture(since=session.started_at)
            if ctx:
                git_context = ctx.to_summary()
                self.db.add_capture(session.id, "git_end", git_context, ctx.to_json())

        summarizer = OllamaSummarizer()
        summary = summarizer.summarize_session(
            git_context=git_context,
            notes=notes,
            captures=captures,
            project_name=project.name,
        )

        self.db.end_session(session.id, summary)
        duration = format_duration(session.started_at, datetime.now())

        return {
            "success": True,
            "duration": duration,
            "summary": summary
        }

    def _handle_note(self, path: Path, args: dict) -> dict:
        """Add a note to current session."""
        note_text = args.get("note", "").strip()
        if not note_text:
            return {"success": False, "error": "Note text required"}

        project = find_project_root(self.db, path)
        if not project:
            return {"success": False, "error": "Project not initialized"}

        session = self.db.get_active_session(project.id)
        if not session:
            # Auto-start session
            session = self.db.create_session(project.id)

        self.db.add_note(session.id, note_text)
        return {"success": True, "message": f"Note added: {note_text}"}

    def _handle_summary(self, path: Path, args: dict) -> dict:
        """Get mid-session summary."""
        project = find_project_root(self.db, path)
        if not project:
            return {"success": False, "error": "Project not initialized"}

        session = self.db.get_active_session(project.id)
        if not session:
            return {"success": False, "error": "No active session"}

        git = GitCapture(Path(project.path))
        notes = [n.content for n in self.db.get_session_notes(session.id)]
        captures = [c.content for c in self.db.get_session_captures(session.id)]
        git_context = ""

        if git.is_git_repo():
            ctx = git.capture(since=session.started_at)
            if ctx:
                git_context = ctx.to_summary()

        summarizer = OllamaSummarizer()
        summary = summarizer.summarize_session(
            git_context=git_context,
            notes=notes,
            captures=captures,
            project_name=project.name,
        )

        return {
            "success": True,
            "duration": format_duration(session.started_at, datetime.now()),
            "notes": notes,
            "summary": summary
        }

    def _handle_resume(self, path: Path, args: dict) -> dict:
        """Get resume context for a project."""
        project = find_project_root(self.db, path)
        if not project:
            return {"success": False, "error": "Project not initialized"}

        last_session = self.db.get_last_session(project.id)
        recent_notes = self.db.get_recent_notes(project.id, limit=5)

        git = GitCapture(Path(project.path))
        git_context = None
        if git.is_git_repo():
            ctx = git.capture()
            if ctx:
                git_context = {
                    "branch": ctx.branch,
                    "modified_files": ctx.modified_files[:10],
                    "has_uncommitted_changes": ctx.has_uncommitted_changes
                }

        return {
            "success": True,
            "project": project.name,
            "last_active": format_time_ago(project.last_active),
            "last_session_summary": last_session.summary if last_session else None,
            "recent_notes": [n.content for n in recent_notes],
            "git": git_context
        }

    def _handle_init(self, path: Path, args: dict) -> dict:
        """Initialize project tracking."""
        project_name = args.get("name") or path.name

        existing = self.db.get_project_by_path(str(path))
        if existing:
            return {
                "success": True,
                "message": f"Project {existing.name} already tracked",
                "project": existing.name
            }

        project = self.db.create_project(project_name, str(path))
        return {
            "success": True,
            "message": f"Initialized {project_name} for context tracking",
            "project": project.name
        }

    def run_stdio(self):
        """Run MCP server over stdio (JSON-RPC)."""
        # Simple JSON-RPC over stdio implementation
        for line in sys.stdin:
            try:
                request = json.loads(line)
                method = request.get("method", "")
                params = request.get("params", {})
                req_id = request.get("id")

                if method == "tools/list":
                    result = {"tools": self.get_tools()}
                elif method == "tools/call":
                    tool_name = params.get("name", "")
                    tool_args = params.get("arguments", {})
                    result = {"content": [{"type": "text", "text": json.dumps(self.call_tool(tool_name, tool_args))}]}
                elif method == "initialize":
                    result = {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "devcontext", "version": "0.1.0"}
                    }
                else:
                    result = {"error": f"Unknown method: {method}"}

                response = {"jsonrpc": "2.0", "id": req_id, "result": result}
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError:
                pass
            except Exception as e:
                if req_id:
                    response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": str(e)}}
                    print(json.dumps(response), flush=True)


def main():
    """Entry point for MCP server."""
    server = DevContextMCPServer()
    server.run_stdio()
