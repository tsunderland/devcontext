# DevContext Integration for Goose

## MCP Server Setup

Goose supports MCP servers natively. Add DevContext to your Goose configuration.

### Configuration

Add to `~/.config/goose/config.yaml`:

```yaml
mcp_servers:
  devcontext:
    command: devctx
    args:
      - mcp-serve
```

Or in `profiles.yaml`:

```yaml
default:
  provider: anthropic
  processor: claude-sonnet
  accelerator: claude-haiku
  moderator: truncate
  toolkits:
    - name: developer
      requires: {}
  mcp_servers:
    devcontext:
      command: devctx
      args:
        - mcp-serve
```

## Available Tools

Once configured, Goose can use:

| Tool | Description |
|------|-------------|
| `devcontext_status` | Check project/session status |
| `devcontext_start` | Start a work session |
| `devcontext_end` | End session with AI summary |
| `devcontext_note` | Add session notes |
| `devcontext_summary` | Get mid-session summary |
| `devcontext_resume` | Get context to resume work |
| `devcontext_init` | Initialize project tracking |

## Workflow

1. **Resume Context**: Ask Goose to check DevContext for previous work
2. **Start Session**: Goose starts tracking at session beginning
3. **Add Notes**: During work, Goose logs important decisions
4. **End Session**: Generate summary of accomplishments

## Example Prompts

```
"Use devcontext to check what I was working on last time"

"Start a devcontext session and then help me implement the auth feature"

"Add a devcontext note that we decided to use JWT instead of sessions"

"End the devcontext session and show me the summary"
```
