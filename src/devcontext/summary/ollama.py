"""Ollama-based summarization for DevContext."""

from typing import Optional

from ..config import get_model


class OllamaSummarizer:
    """Generate summaries using Ollama (local LLM)."""

    def __init__(self, model: Optional[str] = None):
        """Initialize summarizer with optional model override."""
        self.model = model or get_model()
        self._client = None

    @property
    def client(self):
        """Lazy load Ollama client."""
        if self._client is None:
            try:
                import ollama
                self._client = ollama
            except ImportError:
                return None
        return self._client

    def is_available(self) -> bool:
        """Check if Ollama is available and running."""
        if self.client is None:
            return False

        try:
            self.client.list()
            return True
        except Exception:
            return False

    def has_model(self) -> bool:
        """Check if the configured model is available."""
        if not self.is_available():
            return False

        try:
            models = self.client.list()
            model_names = [m.get("name", "").split(":")[0] for m in models.get("models", [])]
            return self.model.split(":")[0] in model_names
        except Exception:
            return False

    def summarize_session(
        self,
        git_context: str,
        notes: list[str],
        captures: list[str],
        project_name: str,
    ) -> Optional[str]:
        """Generate a session summary."""
        if not self.is_available():
            return self._fallback_summary(git_context, notes, captures, project_name)

        prompt = self._build_prompt(git_context, notes, captures, project_name)

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.3,
                    "num_predict": 500,
                }
            )
            return response.get("response", "").strip()
        except Exception as e:
            return self._fallback_summary(git_context, notes, captures, project_name)

    def _build_prompt(
        self,
        git_context: str,
        notes: list[str],
        captures: list[str],
        project_name: str,
    ) -> str:
        """Build the summarization prompt."""
        sections = [f"Project: {project_name}\n"]

        if git_context:
            sections.append(f"Git Activity:\n{git_context}\n")

        if notes:
            sections.append("Developer Notes:\n" + "\n".join(f"- {n}" for n in notes) + "\n")

        if captures:
            sections.append("Activity Log:\n" + "\n".join(captures[:20]) + "\n")

        context = "\n".join(sections)

        return f"""You are a helpful assistant that summarizes developer work sessions.

Given the following context from a coding session, provide a brief summary that will help the developer quickly resume their work later.

Focus on:
1. What was being worked on (specific features, bugs, files)
2. What was accomplished
3. What is still incomplete or blocked
4. Suggested next steps

Keep the summary concise (3-5 sentences) and actionable.

Context:
{context}

Summary:"""

    def _fallback_summary(
        self,
        git_context: str,
        notes: list[str],
        captures: list[str],
        project_name: str,
    ) -> str:
        """Generate a basic summary without AI."""
        parts = [f"Session on {project_name}"]

        if notes:
            parts.append(f"\nNotes: {'; '.join(notes[:3])}")

        if "commits" in git_context.lower():
            parts.append("\nGit activity recorded.")

        return "".join(parts)

    def generate_resume_prompt(
        self,
        last_summary: str,
        recent_notes: list[str],
        git_context: str,
        time_away: str,
    ) -> Optional[str]:
        """Generate a resume context for returning to a project."""
        if not self.is_available():
            return self._fallback_resume(last_summary, recent_notes, time_away)

        prompt = f"""You are helping a developer resume work on a project after being away for {time_away}.

Last session summary:
{last_summary}

Recent notes:
{chr(10).join(f'- {n}' for n in recent_notes) if recent_notes else 'None'}

Current git state:
{git_context}

Provide a brief, actionable summary to help them get back up to speed quickly. Focus on:
1. Where they left off
2. What needs attention
3. Immediate next step

Keep it to 2-3 sentences."""

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.3,
                    "num_predict": 300,
                }
            )
            return response.get("response", "").strip()
        except Exception:
            return self._fallback_resume(last_summary, recent_notes, time_away)

    def _fallback_resume(
        self,
        last_summary: str,
        recent_notes: list[str],
        time_away: str,
    ) -> str:
        """Generate basic resume prompt without AI."""
        parts = [f"You've been away for {time_away}."]

        if last_summary:
            parts.append(f"\nLast session: {last_summary[:200]}")

        if recent_notes:
            parts.append(f"\nRecent notes: {recent_notes[0]}")

        return "".join(parts)
