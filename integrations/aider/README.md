# DevContext Integration for Aider

## Setup

Add DevContext commands to your Aider workflow for session tracking.

### Option 1: Shell Wrapper

Create a wrapper script `aider-tracked`:

```bash
#!/bin/bash
# Start DevContext session
devctx start 2>/dev/null || devctx init && devctx start

# Run Aider
aider "$@"

# End session with summary
devctx end
```

### Option 2: Manual Commands

Start your session:
```bash
devctx start
aider
```

Add notes during work:
```bash
devctx note "Refactored auth module"
```

End your session:
```bash
devctx end
```

### Option 3: Aider In-Chat Commands

From within Aider, run shell commands:
```
/run devctx note "Implemented feature X"
/run devctx summary
```

## Context for New Sessions

Before starting work, get context:
```bash
devctx resume
```

This shows:
- Last session summary
- Recent notes
- Current git status
- Suggested next steps

## Tips

- Initialize once per project: `devctx init`
- Notes persist across Aider sessions
- Summaries capture all git commits made
