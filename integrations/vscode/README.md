# DevContext Integration for VS Code

## Task Runner Setup

Add DevContext commands as VS Code tasks.

### tasks.json

Add to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "DevContext: Start Session",
      "type": "shell",
      "command": "devctx start",
      "problemMatcher": [],
      "presentation": {
        "reveal": "silent",
        "panel": "shared"
      }
    },
    {
      "label": "DevContext: End Session",
      "type": "shell",
      "command": "devctx end",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "shared"
      }
    },
    {
      "label": "DevContext: Add Note",
      "type": "shell",
      "command": "devctx note \"${input:noteText}\"",
      "problemMatcher": [],
      "presentation": {
        "reveal": "silent",
        "panel": "shared"
      }
    },
    {
      "label": "DevContext: Resume",
      "type": "shell",
      "command": "devctx resume",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "shared"
      }
    },
    {
      "label": "DevContext: Status",
      "type": "shell",
      "command": "devctx status",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "shared"
      }
    },
    {
      "label": "DevContext: Summary",
      "type": "shell",
      "command": "devctx summary",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "shared"
      }
    }
  ],
  "inputs": [
    {
      "id": "noteText",
      "type": "promptString",
      "description": "Enter note text"
    }
  ]
}
```

### Keybindings (Optional)

Add to `keybindings.json`:

```json
[
  {
    "key": "ctrl+shift+d s",
    "command": "workbench.action.tasks.runTask",
    "args": "DevContext: Start Session"
  },
  {
    "key": "ctrl+shift+d e",
    "command": "workbench.action.tasks.runTask",
    "args": "DevContext: End Session"
  },
  {
    "key": "ctrl+shift+d n",
    "command": "workbench.action.tasks.runTask",
    "args": "DevContext: Add Note"
  },
  {
    "key": "ctrl+shift+d r",
    "command": "workbench.action.tasks.runTask",
    "args": "DevContext: Resume"
  }
]
```

## Usage

1. Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`)
2. Type "Tasks: Run Task"
3. Select the DevContext task

Or use keybindings if configured:
- `Ctrl+Shift+D S` - Start session
- `Ctrl+Shift+D E` - End session
- `Ctrl+Shift+D N` - Add note
- `Ctrl+Shift+D R` - Resume

## Copilot Integration

When using GitHub Copilot Chat:

1. Run `devctx resume` to get context
2. Paste the summary into Copilot Chat for context
3. Use `devctx note` to record decisions made with Copilot

## Extension Idea

A dedicated VS Code extension could:
- Auto-start sessions when opening a project
- Show session status in status bar
- Integrate notes with Copilot context

Contributions welcome at github.com/tsunderland/devcontext
