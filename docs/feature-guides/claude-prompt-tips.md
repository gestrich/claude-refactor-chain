# Claude Prompt Tips

Best practices for writing effective prompts and configuring Claude Code for reliable automated workflows.

## Table of Contents

- [Build Tooling Before Claude Runs](#build-tooling-before-claude-runs)
- [Enforce Critical Tool Success](#enforce-critical-tool-success)
- [Using Custom Commands](#using-custom-commands)
- [Working Directory Restrictions](#working-directory-restrictions)

---

## Build Tooling Before Claude Runs

If your task requires custom tooling (scripts, binaries, dependencies), build them **before** Claude Code runs rather than asking Claude to build them.

### Why This Matters

When Claude encounters a missing tool or build failure, it will attempt workarounds:
- Trying alternative approaches
- Modifying code to skip the failing step
- Making assumptions about what the tool would have done

This wastes time and tokens, and often produces incorrect results. **Fail fast instead.**

### Solution: Pre-build in Your Workflow

**Option 1: GitHub Workflow Step**

Add a build step before the ClaudeChain action:

```yaml
- name: Build custom tooling
  run: |
    cd scripts
    swift build -c release
    cp .build/release/my-tool /usr/local/bin/

- name: Run ClaudeChain
  uses: gestrich/claude-chain@main
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

**Option 2: Pre-action Script**

Create a `pre-action.sh` script in your project directory:

```bash
#!/bin/bash
# claude-chain/my-project/pre-action.sh
set -e

echo "Building required tooling..."
cd "$GITHUB_WORKSPACE/scripts"
swift build -c release

echo "Installing to PATH..."
cp .build/release/my-tool /usr/local/bin/
```

See [Pre/Post Action Scripts](./projects.md#prepost-action-scripts) for details.

### Benefits

- Immediate failure if tooling can't be built
- Clear error messages in workflow logs
- No wasted Claude API costs on doomed attempts
- Predictable, reproducible builds

---

## Enforce Critical Tool Success

When your prompt includes tools that **must succeed** for the task to be valid, use explicit language to prevent Claude from working around failures.

### The Problem

Claude is helpful and will try to make progress even when things fail. If a critical validation tool fails, Claude might:
- Skip the validation step
- Assume the validation would have passed
- Continue with subsequent steps anyway

### Solution: Use MUST Language

In your prompt or spec.md, be explicit about critical requirements:

```markdown
## Critical Requirements

The following tools are CRITICAL and MUST succeed:

1. **my-validation-script.sh** - MUST return exit code 0
2. **xcodegen** - MUST complete without errors

### MANDATORY Rules

- You MUST check the exit code of every critical tool
- If a critical tool returns a non-zero exit code, you MUST STOP IMMEDIATELY
- You MUST NOT continue to subsequent steps after a critical failure
- You MUST NOT implement workarounds to avoid running the tools
- You MUST report the error details and STOP

### On Failure

If a critical tool fails:
1. Read the full log/output to understand the error
2. Include the error details in your response
3. STOP - do not proceed with any further steps
```

### Include Error Details in Output

Ask Claude to log errors so they appear in the structured output:

```markdown
If any step fails, you MUST include:
- The exact command that failed
- The exit code
- The full error output

This ensures the error details are captured in your JSON response.
```

This makes debugging easier since the error message will appear in:
- The workflow logs
- The Slack notification (if configured)
- The structured output JSON

---

## Using Custom Commands

Claude Code's slash commands (like `/commit`) don't work in automated GitHub Actions environments. Instead, reference your command files directly.

### The Problem

If your prompt says:
```
Run /my-custom-command to validate the changes
```

Claude won't be able to execute this—slash commands require the interactive Claude Code CLI.

### Solution: Reference the File Path

Instead of using slash command syntax, tell Claude where to find the command instructions:

```markdown
Before completing the task, follow the instructions in
`.claude/commands/my-custom-command.md` to validate your changes.
```

Or include the command content directly in your prompt:

```markdown
## Validation Steps

After making changes, perform these validation steps:

1. Run the linter: `npm run lint`
2. Run tests: `npm test`
3. Verify types: `npm run typecheck`
```

### Organizing Commands for Automation

If you have commands you want to use in both interactive and automated contexts:

```
.claude/
  commands/
    validate-changes.md    # Can be referenced by path in prompts
    build-and-test.md      # Can be referenced by path in prompts
```

In your spec.md or prompt:
```markdown
After implementing the task, follow the validation steps in
`.claude/commands/validate-changes.md`.
```

Claude will read the file and follow its instructions.

---

## Working Directory Restrictions

Claude Code has security restrictions that prevent using `cat` (and similar commands) to read files outside the working directory where Claude Code is running.

### The Problem

If your workflow writes files to `/tmp` or another directory outside the project:

```bash
# This will fail in Claude Code
echo "results" > /tmp/output.txt
cat /tmp/output.txt  # ❌ Blocked - outside working directory
```

Claude Code restricts file access to the current working directory for security reasons.

### Solution: Use the Working Directory

Write temporary files within the project directory instead:

```bash
# Use a local temp directory
mkdir -p .tmp
echo "results" > .tmp/output.txt
cat .tmp/output.txt  # ✅ Works
```

Or use the scratchpad directory if available in the Claude Code environment.

### In Your Prompts

If your task involves temporary files, be explicit:

```markdown
When writing temporary files, always write them within the current
working directory (e.g., `.tmp/` folder). Do not use `/tmp` or other
system directories as Claude Code cannot read files outside the
working directory.
```

---

## Quick Reference

| Tip | Do | Don't |
|-----|-----|-------|
| Tooling | Build before Claude runs | Ask Claude to build tools |
| Critical tools | Use MUST/STOP language | Hope Claude checks exit codes |
| Error details | Request explicit logging | Assume errors will be captured |
| Custom commands | Reference file path | Use slash command syntax |
| Temp files | Write to working directory | Write to `/tmp` or outside dirs |

---

## Next Steps

- [Projects Guide](./projects.md) - Project configuration including pre/post scripts
- [Troubleshooting](./troubleshooting.md) - Common issues and solutions
- [How It Works](./how-it-works.md) - Understanding the workflow
