# DevContext Integration for Claude Code

## Automatic Context Management

DevContext tracks your work sessions automatically. When working on this project:

1. **Session Start**: DevContext captures your starting git state
2. **Notes**: Add notes during your session with `devctx note "your note"`
3. **Session End**: Get an AI-generated summary of what was accomplished

## MCP Server Integration

Add to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "devcontext": {
      "command": "devctx",
      "args": ["mcp-serve"]
    }
  }
}
```

## Available Tools

Once configured, Claude Code can use these tools:

- `devcontext_status` - Check project/session status
- `devcontext_start` - Start a work session
- `devcontext_end` - End session with summary
- `devcontext_note` - Add session notes
- `devcontext_summary` - Mid-session summary
- `devcontext_resume` - Get context to resume work
- `devcontext_init` - Initialize project tracking

## Suggested Workflow

At session start:
```
Use devcontext_resume to check what was worked on previously.
Then devcontext_start to begin tracking this session.
```

During work:
```
Use devcontext_note to record decisions, blockers, or next steps.
```

At session end:
```
Use devcontext_end to generate and save a session summary.
```

## Tips

- DevContext works from any subdirectory of the project
- Notes are automatically timestamped
- Summaries include git activity (commits, files changed)
- All data stored locally in `~/.devcontext/`
