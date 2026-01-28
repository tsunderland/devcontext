# DevContext

**Resume any project in 30 seconds.**

> An open source CLI that captures your work context so you never lose track of what you were doing.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## The Problem

You have 20 projects. You context-switch constantly. Every time you return to a project, you spend 20-30 minutes figuring out:

- What was I working on?
- What's broken?
- What's the next step?

This costs developers **$50K/year** in lost productivity.

## The Solution

DevContext runs in the background and captures your work context:

- **Git activity** - commits, branches, diffs
- **Session notes** - quick bookmarks as you work
- **AI summaries** - automatic session summaries via local LLM

When you return to a project, get an instant catch-up:

```bash
$ devctx resume myproject

📁 myproject (last active: 3 days ago)

🔄 Last Session Summary:
You were implementing the authentication flow. The login form is complete
but the JWT token refresh is failing with a 401 error. You suspected the
issue is in src/auth/refresh.ts around line 45.

📝 Your Notes:
- "JWT refresh broken, check token expiry logic"
- "Need to add error boundary for auth failures"

📂 Files You Were Editing:
- src/auth/refresh.ts (15 changes)
- src/components/LoginForm.tsx (8 changes)
- tests/auth.test.ts (3 changes)

⏭️ Suggested Next Step:
Debug the JWT refresh in src/auth/refresh.ts:45
```

## Features

- **100% Offline** - Uses Ollama for local AI, no cloud required
- **Privacy First** - All data stays on your machine
- **Zero Config** - Works out of the box with sensible defaults
- **Git Native** - Integrates seamlessly with your git workflow
- **Language Agnostic** - Works with any project, any language

## Installation

### Recommended: pipx (isolated install)

```bash
# Install pipx if you don't have it
brew install pipx
pipx ensurepath

# Install devcontext
pipx install devcontext
```

### Alternative: uv tool

```bash
# Install with uv (fast, isolated)
uv tool install devcontext
```

### Verify installation

```bash
devctx --version
```

### Prerequisites

For AI-powered summaries, install [Ollama](https://ollama.ai):

```bash
# macOS
brew install ollama

# Then pull a model
ollama pull llama3.1
```

DevContext works without Ollama, but summaries will be disabled.

## Quick Start

```bash
# Start tracking a project
cd ~/myproject
devctx init

# Begin a work session
devctx start

# ... do your work ...

# Add notes as you go
devctx note "Fixed the login bug, now working on signup"

# End your session (generates summary)
devctx end

# Later, resume with full context
devctx resume
```

## Commands

| Command | Description |
|---------|-------------|
| `devctx init` | Initialize tracking for current project |
| `devctx start` | Begin a new work session |
| `devctx end` | End session and generate summary |
| `devctx note <text>` | Add a quick note to current session |
| `devctx resume` | Get context summary for current project |
| `devctx list` | List all tracked projects |
| `devctx status` | Show current session status |
| `devctx history` | View session history for project |

## Configuration

Config file: `~/.config/devcontext/config.toml`

```toml
[general]
# Ollama model for summaries
model = "llama3.1"

# Auto-start session on git activity
auto_start = true

# Capture terminal history (opt-in)
capture_terminal = false

[display]
# Rich formatting
color = true
emoji = true
```

## How It Works

1. **Capture**: DevContext watches for git activity and stores context in a local SQLite database
2. **Summarize**: When you end a session, Ollama generates a concise summary
3. **Resume**: Context is retrieved and formatted for quick scanning

All data is stored in `~/.local/share/devcontext/`.

## Support the Project

DevContext is **free and open source** (MIT License).

If it saves you time, consider supporting development:

- ⭐ **Star this repo** - Helps others discover it
- 💬 **Report issues** - Help us improve
- 🤝 **Contribute** - PRs welcome!
- ☕ **Sponsor** - [GitHub Sponsors](https://github.com/sponsors/tsunderland)

### Commercial Use

Using DevContext at work? Consider a support subscription to fund continued development:

- **Pro Support** ($50/mo) - Priority email support, screen share sessions
- **Enterprise** ($500/mo) - Dedicated Slack channel, custom integrations

Contact: hello@bitfuturistic.com

## Philosophy

We believe developer tools should be:

1. **Offline first** - Your data, your machine
2. **Open source** - Transparent and trustworthy
3. **Simple** - Do one thing well
4. **Respectful** - No telemetry, no tracking

## Roadmap

- [x] Core CLI with git integration
- [x] Ollama-powered summaries
- [ ] VS Code extension
- [ ] Neovim plugin
- [ ] Team sync (opt-in, self-hosted)
- [ ] Browser extension for research context

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built with ❤️ by [Bitfuturistic Solutions](https://bitfuturistic.com)**
