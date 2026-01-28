"""Git context capture for DevContext."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from git import InvalidGitRepositoryError, Repo
from git.objects import Commit


@dataclass
class GitContext:
    """Captured git context."""
    branch: str
    recent_commits: list[dict]
    modified_files: list[str]
    staged_files: list[str]
    untracked_files: list[str]
    has_uncommitted_changes: bool

    def to_summary(self) -> str:
        """Generate a human-readable summary."""
        lines = [f"Branch: {self.branch}"]

        if self.recent_commits:
            lines.append(f"\nRecent commits ({len(self.recent_commits)}):")
            for commit in self.recent_commits[:5]:
                lines.append(f"  - {commit['message'][:60]}")

        if self.modified_files:
            lines.append(f"\nModified files ({len(self.modified_files)}):")
            for f in self.modified_files[:10]:
                lines.append(f"  - {f}")
            if len(self.modified_files) > 10:
                lines.append(f"  ... and {len(self.modified_files) - 10} more")

        if self.staged_files:
            lines.append(f"\nStaged files ({len(self.staged_files)}):")
            for f in self.staged_files[:5]:
                lines.append(f"  - {f}")

        if self.has_uncommitted_changes:
            lines.append("\n⚠️  Uncommitted changes present")

        return "\n".join(lines)

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps({
            "branch": self.branch,
            "recent_commits": self.recent_commits,
            "modified_files": self.modified_files,
            "staged_files": self.staged_files,
            "untracked_files": self.untracked_files,
            "has_uncommitted_changes": self.has_uncommitted_changes,
        })


class GitCapture:
    """Captures git context from a repository."""

    def __init__(self, repo_path: Optional[Path] = None):
        """Initialize with repository path."""
        self.repo_path = repo_path or Path.cwd()
        self._repo: Optional[Repo] = None

    @property
    def repo(self) -> Optional[Repo]:
        """Get the git repository, or None if not a git repo."""
        if self._repo is None:
            try:
                self._repo = Repo(self.repo_path, search_parent_directories=True)
            except InvalidGitRepositoryError:
                return None
        return self._repo

    def is_git_repo(self) -> bool:
        """Check if current path is a git repository."""
        return self.repo is not None

    def get_branch(self) -> str:
        """Get current branch name."""
        if not self.repo:
            return "unknown"
        try:
            return self.repo.active_branch.name
        except TypeError:
            # Detached HEAD
            return f"detached@{self.repo.head.commit.hexsha[:7]}"

    def get_recent_commits(self, limit: int = 10, since: Optional[datetime] = None) -> list[dict]:
        """Get recent commits."""
        if not self.repo:
            return []

        commits = []
        try:
            for commit in self.repo.iter_commits(max_count=limit):
                if since and commit.authored_datetime.replace(tzinfo=None) < since:
                    break
                commits.append({
                    "sha": commit.hexsha[:7],
                    "message": commit.message.strip().split("\n")[0],
                    "author": str(commit.author),
                    "date": commit.authored_datetime.isoformat(),
                    "files_changed": len(commit.stats.files),
                })
        except Exception:
            pass

        return commits

    def get_modified_files(self) -> list[str]:
        """Get list of modified (unstaged) files."""
        if not self.repo:
            return []

        return [item.a_path for item in self.repo.index.diff(None)]

    def get_staged_files(self) -> list[str]:
        """Get list of staged files."""
        if not self.repo:
            return []

        return [item.a_path for item in self.repo.index.diff("HEAD")]

    def get_untracked_files(self) -> list[str]:
        """Get list of untracked files."""
        if not self.repo:
            return []

        return self.repo.untracked_files

    def has_uncommitted_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        if not self.repo:
            return False

        return self.repo.is_dirty(untracked_files=True)

    def capture(self, since: Optional[datetime] = None) -> Optional[GitContext]:
        """Capture full git context."""
        if not self.is_git_repo():
            return None

        return GitContext(
            branch=self.get_branch(),
            recent_commits=self.get_recent_commits(since=since),
            modified_files=self.get_modified_files(),
            staged_files=self.get_staged_files(),
            untracked_files=self.get_untracked_files(),
            has_uncommitted_changes=self.has_uncommitted_changes(),
        )

    def get_diff_summary(self, max_lines: int = 100) -> str:
        """Get a summary of current changes."""
        if not self.repo:
            return ""

        try:
            diff = self.repo.git.diff(stat=True)
            lines = diff.split("\n")
            if len(lines) > max_lines:
                return "\n".join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines)"
            return diff
        except Exception:
            return ""
