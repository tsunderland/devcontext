"""DevContext CLI - Resume any project in 30 seconds."""

import shutil
import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import __version__
from .capture import GitCapture
from .config import use_emoji, get_model, DATA_DIR
from .db import Database
from .summary import OllamaSummarizer
from .utils import format_time_ago, format_duration

console = Console()


# Emoji helpers
def e(emoji: str, fallback: str = "") -> str:
    """Return emoji if enabled, otherwise fallback."""
    return emoji if use_emoji() else fallback


def find_project_root(db: Database, start_path: Path) -> Optional[tuple]:
    """Find project root by walking up directory tree.

    Returns (project, is_child) tuple where is_child indicates if we're in a subdirectory.
    """
    current = start_path.resolve()

    # First check exact match
    project = db.get_project_by_path(str(current))
    if project:
        return (project, False)

    # Walk up to find parent project
    for parent in current.parents:
        project = db.get_project_by_path(str(parent))
        if project:
            return (project, True)

    return None


@click.group()
@click.version_option(version=__version__, prog_name="devcontext")
def main():
    """DevContext - Resume any project in 30 seconds.

    Track your work context automatically and get instant catch-up
    summaries when you return to a project.
    """
    pass


@main.command()
@click.option("--name", "-n", help="Project name (defaults to directory name)")
def init(name: Optional[str]):
    """Initialize DevContext tracking for current project."""
    cwd = Path.cwd()
    project_name = name or cwd.name

    db = Database()
    existing = db.get_project_by_path(str(cwd))

    if existing:
        console.print(f"{e('📁')} Project [bold]{existing.name}[/bold] already tracked.")
        console.print(f"   Last active: {format_time_ago(existing.last_active)}")
        return

    # Check if it's a git repo
    git = GitCapture(cwd)
    if not git.is_git_repo():
        console.print(f"{e('⚠️', '!')} Warning: Not a git repository. Git tracking disabled.")

    project = db.create_project(project_name, str(cwd))
    console.print(f"{e('✅')} Initialized [bold]{project_name}[/bold] for context tracking.")
    console.print(f"   Run [bold]devctx start[/bold] to begin a session.")


@main.command()
def start():
    """Start a new work session."""
    cwd = Path.cwd()
    db = Database()
    result = find_project_root(db, cwd)

    if not result:
        console.print(f"{e('❌')} Project not initialized. Run [bold]devctx init[/bold] first.")
        return

    project, is_child = result
    if is_child:
        console.print(f"{e('📁')} Using parent project: [bold]{project.name}[/bold]")

    # Check for existing active session
    active = db.get_active_session(project.id)
    if active:
        duration = format_duration(active.started_at, datetime.now())
        console.print(f"{e('⚡')} Session already active ({duration}).")
        console.print(f"   Use [bold]devctx note[/bold] to add notes or [bold]devctx end[/bold] to finish.")
        return

    # Capture initial git state
    git = GitCapture(cwd)
    session = db.create_session(project.id)

    if git.is_git_repo():
        context = git.capture()
        if context:
            db.add_capture(
                session.id,
                "git_start",
                context.to_summary(),
                context.to_json()
            )

    console.print(f"{e('🚀')} Session started for [bold]{project.name}[/bold]")
    console.print(f"   Branch: {git.get_branch() if git.is_git_repo() else 'N/A'}")
    console.print(f"\n   {e('💡')} Add notes: [bold]devctx note \"your note here\"[/bold]")


@main.command()
def end():
    """End current session and generate summary."""
    cwd = Path.cwd()
    db = Database()
    result = find_project_root(db, cwd)

    if not result:
        console.print(f"{e('❌')} Project not initialized. Run [bold]devctx init[/bold] first.")
        return

    project, _ = result

    session = db.get_active_session(project.id)
    if not session:
        console.print(f"{e('ℹ️', 'i')} No active session.")
        return

    # Capture final git state
    git = GitCapture(cwd)
    if git.is_git_repo():
        context = git.capture(since=session.started_at)
        if context:
            db.add_capture(
                session.id,
                "git_end",
                context.to_summary(),
                context.to_json()
            )

    # Gather context for summary
    notes = [n.content for n in db.get_session_notes(session.id)]
    captures = [c.content for c in db.get_session_captures(session.id)]
    git_context = git.capture().to_summary() if git.is_git_repo() and git.capture() else ""

    # Generate summary
    summarizer = OllamaSummarizer()
    console.print(f"{e('🤖')} Generating session summary...")

    summary = summarizer.summarize_session(
        git_context=git_context,
        notes=notes,
        captures=captures,
        project_name=project.name,
    )

    db.end_session(session.id, summary)

    duration = format_duration(session.started_at, datetime.now())
    console.print(f"\n{e('✅')} Session ended ({duration})")

    if summary:
        console.print(Panel(summary, title="Session Summary", border_style="green"))


@main.command()
@click.argument("text", nargs=-1, required=True)
def note(text: tuple[str, ...]):
    """Add a note to current session."""
    cwd = Path.cwd()
    db = Database()
    result = find_project_root(db, cwd)

    if not result:
        console.print(f"{e('❌')} Project not initialized. Run [bold]devctx init[/bold] first.")
        return

    project, _ = result

    session = db.get_active_session(project.id)
    if not session:
        console.print(f"{e('ℹ️', 'i')} No active session. Starting one...")
        session = db.create_session(project.id)

    note_text = " ".join(text)
    db.add_note(session.id, note_text)
    console.print(f"{e('📝')} Note added: {note_text}")


@main.command()
def resume():
    """Get context summary for current project."""
    cwd = Path.cwd()
    db = Database()
    result = find_project_root(db, cwd)

    if not result:
        console.print(f"{e('❌')} Project not initialized. Run [bold]devctx init[/bold] first.")
        return

    project, _ = result

    # Get last session
    last_session = db.get_last_session(project.id)
    recent_notes = db.get_recent_notes(project.id, limit=5)

    # Current git state
    git = GitCapture(cwd)
    git_context = git.capture()

    time_away = format_time_ago(project.last_active)

    console.print(Panel(
        f"[bold]{project.name}[/bold]\nLast active: {time_away}",
        title=f"{e('📁')} Project",
        border_style="blue"
    ))

    # Last session summary
    if last_session and last_session.summary:
        console.print(Panel(
            last_session.summary,
            title=f"{e('🔄')} Last Session",
            border_style="green"
        ))

    # Recent notes
    if recent_notes:
        notes_text = "\n".join(f"• {n.content}" for n in recent_notes)
        console.print(Panel(
            notes_text,
            title=f"{e('📝')} Recent Notes",
            border_style="yellow"
        ))

    # Git status
    if git_context:
        git_info = []
        git_info.append(f"Branch: [bold]{git_context.branch}[/bold]")
        if git_context.modified_files:
            git_info.append(f"Modified: {len(git_context.modified_files)} files")
        if git_context.has_uncommitted_changes:
            git_info.append(f"{e('⚠️', '!')} Uncommitted changes")

        console.print(Panel(
            "\n".join(git_info),
            title=f"{e('🔀')} Git Status",
            border_style="cyan"
        ))

    # AI-powered resume prompt
    if last_session and last_session.summary:
        summarizer = OllamaSummarizer()
        if summarizer.is_available():
            resume_prompt = summarizer.generate_resume_prompt(
                last_summary=last_session.summary,
                recent_notes=[n.content for n in recent_notes],
                git_context=git_context.to_summary() if git_context else "",
                time_away=time_away,
            )
            if resume_prompt:
                console.print(Panel(
                    resume_prompt,
                    title=f"{e('⏭️')} Suggested Next Step",
                    border_style="magenta"
                ))


@main.command()
def status():
    """Show current session status."""
    cwd = Path.cwd()
    db = Database()
    result = find_project_root(db, cwd)

    if not result:
        console.print(f"{e('❌')} Project not initialized. Run [bold]devctx init[/bold] first.")
        return

    project, _ = result

    session = db.get_active_session(project.id)

    console.print(f"\n{e('📁')} Project: [bold]{project.name}[/bold]")

    if session:
        duration = format_duration(session.started_at, datetime.now())
        notes = db.get_session_notes(session.id)
        captures = db.get_session_captures(session.id)

        console.print(f"{e('⚡')} Session: [green]Active[/green] ({duration})")
        console.print(f"   Notes: {len(notes)}")
        console.print(f"   Captures: {len(captures)}")
    else:
        console.print(f"{e('💤')} Session: [dim]None[/dim]")
        console.print(f"   Last active: {format_time_ago(project.last_active)}")


@main.command(name="list")
def list_projects():
    """List all tracked projects."""
    db = Database()
    projects = db.list_projects()

    if not projects:
        console.print(f"{e('ℹ️', 'i')} No projects tracked yet.")
        console.print(f"   Run [bold]devctx init[/bold] in a project directory.")
        return

    table = Table(title=f"{e('📁')} Tracked Projects")
    table.add_column("Name", style="bold")
    table.add_column("Path")
    table.add_column("Last Active")
    table.add_column("Status")

    for project in projects:
        active_session = db.get_active_session(project.id)
        status = "[green]Active[/green]" if active_session else "[dim]Idle[/dim]"

        table.add_row(
            project.name,
            project.path,
            format_time_ago(project.last_active),
            status,
        )

    console.print(table)


@main.command()
@click.argument("project_name", required=False)
@click.option("--limit", "-l", default=5, help="Number of sessions to show")
def history(project_name: Optional[str], limit: int):
    """View session history for a project."""
    cwd = Path.cwd()
    db = Database()

    if project_name:
        projects = db.list_projects()
        project = next((p for p in projects if p.name == project_name), None)
        if not project:
            console.print(f"{e('❌')} Project '{project_name}' not found.")
            return
    else:
        result = find_project_root(db, cwd)
        if not result:
            console.print(f"{e('❌')} Project not initialized. Run [bold]devctx init[/bold] first.")
            return
        project, _ = result

    sessions = db.get_recent_sessions(project.id, limit=limit)

    if not sessions:
        console.print(f"{e('ℹ️', 'i')} No session history for [bold]{project.name}[/bold].")
        return

    console.print(f"\n{e('📜')} Session History: [bold]{project.name}[/bold]\n")

    for session in sessions:
        if session.ended_at:
            duration = format_duration(session.started_at, session.ended_at)
            time_str = format_time_ago(session.ended_at)
        else:
            duration = format_duration(session.started_at, datetime.now())
            time_str = "[green]Active[/green]"

        console.print(f"[bold]{time_str}[/bold] ({duration})")

        if session.summary:
            console.print(f"   {session.summary[:100]}...")

        notes = db.get_session_notes(session.id)
        if notes:
            console.print(f"   {e('📝')} {len(notes)} note(s)")

        console.print()


@main.command()
def doctor():
    """Check system health and dependencies."""
    console.print(f"\n{e('🩺')} DevContext Health Check\n")

    all_ok = True

    # Check database
    try:
        db = Database()
        projects = db.list_projects()
        console.print(f"{e('✅', '[OK]')} Database: {len(projects)} project(s) tracked")
    except Exception as ex:
        console.print(f"{e('❌', '[ERR]')} Database: {ex}")
        all_ok = False

    # Check data directory
    if DATA_DIR.exists():
        console.print(f"{e('✅', '[OK]')} Data directory: {DATA_DIR}")
    else:
        console.print(f"{e('⚠️', '[WARN]')} Data directory not created yet")

    # Check Ollama installed
    ollama_path = shutil.which("ollama")
    if ollama_path:
        console.print(f"{e('✅', '[OK]')} Ollama binary: {ollama_path}")
    else:
        console.print(f"{e('❌', '[ERR]')} Ollama: Not installed")
        console.print(f"         Install from: https://ollama.ai")
        all_ok = False

    # Check Ollama running
    summarizer = OllamaSummarizer()
    if summarizer.is_available():
        console.print(f"{e('✅', '[OK]')} Ollama service: Running")

        # Check model
        model = get_model()
        if summarizer.has_model():
            console.print(f"{e('✅', '[OK]')} Model: {model} available")
        else:
            console.print(f"{e('❌', '[ERR]')} Model: {model} not found")
            console.print(f"         Run: ollama pull {model}")
            all_ok = False
    else:
        console.print(f"{e('❌', '[ERR]')} Ollama service: Not running")
        console.print(f"         Run: ollama serve")
        all_ok = False

    # Check git
    git_path = shutil.which("git")
    if git_path:
        console.print(f"{e('✅', '[OK]')} Git: {git_path}")
    else:
        console.print(f"{e('⚠️', '[WARN]')} Git: Not found (git features disabled)")

    console.print()
    if all_ok:
        console.print(f"{e('🎉')} All systems operational!")
    else:
        console.print(f"{e('⚠️', '!')} Some issues found. AI summaries may be limited.")


@main.command()
def summary():
    """Generate summary of current session (without ending it)."""
    cwd = Path.cwd()
    db = Database()
    result = find_project_root(db, cwd)

    if not result:
        console.print(f"{e('❌')} Project not initialized. Run [bold]devctx init[/bold] first.")
        return

    project, _ = result
    session = db.get_active_session(project.id)

    if not session:
        console.print(f"{e('ℹ️', 'i')} No active session. Use [bold]devctx resume[/bold] to see last session.")
        return

    # Gather context
    git = GitCapture(Path(project.path))
    notes = [n.content for n in db.get_session_notes(session.id)]
    captures = [c.content for c in db.get_session_captures(session.id)]
    git_context = ""
    if git.is_git_repo():
        ctx = git.capture(since=session.started_at)
        if ctx:
            git_context = ctx.to_summary()

    duration = format_duration(session.started_at, datetime.now())
    console.print(f"\n{e('📊')} Session Summary for [bold]{project.name}[/bold] ({duration})\n")

    # Show notes
    if notes:
        console.print(Panel(
            "\n".join(f"• {n}" for n in notes),
            title=f"{e('📝')} Notes ({len(notes)})",
            border_style="yellow"
        ))

    # Show git activity
    if git_context:
        console.print(Panel(
            git_context,
            title=f"{e('🔀')} Git Activity",
            border_style="cyan"
        ))

    # Generate AI summary
    summarizer = OllamaSummarizer()
    if summarizer.is_available():
        console.print(f"{e('🤖')} Generating AI summary...")
        ai_summary = summarizer.summarize_session(
            git_context=git_context,
            notes=notes,
            captures=captures,
            project_name=project.name,
        )
        if ai_summary:
            console.print(Panel(
                ai_summary,
                title=f"{e('🧠')} AI Summary",
                border_style="green"
            ))
    else:
        console.print(f"\n{e('💡')} Tip: Run [bold]devctx doctor[/bold] to check Ollama setup for AI summaries.")


@main.command()
def support():
    """Support DevContext development."""
    console.print(Panel(
        """[bold]Thank you for considering supporting DevContext![/bold]

DevContext is free and open source (MIT License).
Your support helps fund continued development.

[bold]Ways to support:[/bold]

{star} Star the repo
   github.com/tsunderland/devcontext

{sponsor} GitHub Sponsors
   github.com/sponsors/tsunderland

{coffee} Buy me a coffee
   ko-fi.com/bitfuturistic

{enterprise} Commercial Support
   tsunderland@bitfuturistic.com

[dim]Every contribution helps, no matter how small![/dim]
""".format(
    star=e('⭐', '*'),
    sponsor=e('💖', '<3'),
    coffee=e('☕', 'o'),
    enterprise=e('🏢', '#'),
),
        title="Support DevContext",
        border_style="magenta",
    ))

    if click.confirm("\nOpen GitHub Sponsors page?", default=False):
        webbrowser.open("https://github.com/sponsors/tsunderland")


@main.command(name="mcp-serve")
def mcp_serve():
    """Run MCP server for AI tool integrations.

    Enables AI coding assistants (Claude Code, Aider, Goose, etc.)
    to manage DevContext sessions programmatically.

    Configure your AI tool to connect via stdio:
        devctx mcp-serve
    """
    from .integrations.mcp_server import main as mcp_main
    mcp_main()


if __name__ == "__main__":
    main()
