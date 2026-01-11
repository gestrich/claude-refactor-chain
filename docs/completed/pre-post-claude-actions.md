# Pre/Post Claude Action Scripts

## Background

Claude Code sometimes doesn't handle script failures well—it may continue working even after a script fails, producing invalid PRs. For example, a refactoring script that runs before Claude Code might fail, but Claude Code proceeds anyway and creates a PR with invalid results.

To address this, we're adding **pre-action** and **post-action** scripts that run before and after Claude Code execution. These are optional bash scripts that:
- Run project-specific setup or cleanup
- Fail fast if something goes wrong (the entire job fails, no PR created)
- Allow users to validate the environment before Claude works, or post-process results after

### Current Flow

```
1. prepare    → generates prompt (tells Claude to commit)
2. Claude Code → implements task, may commit during execution
3. finalize   → commits any leftover changes, creates PR
```

### Proposed Flow

```
1. prepare       → generates prompt (NO commit instruction)
2. pre-action    → run pre-action.sh if exists (fail = abort entire job)
3. Claude Code   → implements task (no committing)
4. post-action   → run post-action.sh if exists (fail = abort entire job)
5. finalize      → commit all changes, create PR
```

### Key Changes

1. **New project files**: `pre-action.sh` and `post-action.sh` in project directory
2. **Remove commit instruction from prompt**: Claude Code should NOT commit during execution
3. **New action steps**: Run pre-action and post-action scripts with fail-fast behavior
4. **Consolidate commits**: All committing happens in finalize step, after post-action

## Phases

- [ ] Phase 1: Update Documentation

Update project documentation to describe the new action script files.

**Files to modify:**
- `docs/feature-guides/projects.md` - Add section about pre/post action scripts
- `CLAUDE.md` - Add note about new project file options if appropriate

**Details:**
- Document `pre-action.sh` and `post-action.sh` as optional project files
- Explain they run before/after Claude Code
- Explain failure behavior (script fails = job fails, no PR created)
- Add examples of use cases (running tests, linting, code generation, etc.)

- [ ] Phase 2: Remove Commit Instruction from Claude Prompt

Modify the prompt generation to remove the instruction telling Claude to commit changes.

**Files to modify:**
- `src/claudechain/cli/commands/prepare.py` - Remove commit instruction from prompt

**Current prompt ending:**
```
Now complete the task '{task}' following all the details and instructions in the spec.md file above. When you're done, use git add and git commit to commit your changes.
```

**New prompt ending:**
```
Now complete the task '{task}' following all the details and instructions in the spec.md file above.
```

**Important consideration:**
- The default allowed tools in `constants.py` includes `Bash(git add:*),Bash(git commit:*)` - we should keep these available since Claude may still need to stage/commit as part of the task work itself (e.g., if the task involves git operations). The key change is just removing the explicit instruction to commit at the end.

- [ ] Phase 3: Add Action Script Execution Infrastructure

Create infrastructure for running action scripts with proper error handling.

**Files to create:**
- `src/claudechain/infrastructure/actions/__init__.py`
- `src/claudechain/infrastructure/actions/script_runner.py`

**ScriptRunner responsibilities:**
- Check if action script exists at given path
- Run bash script with proper error handling
- Capture stdout/stderr for logging
- Return success/failure status
- Make script executable if needed (chmod +x)

**Function signature:**
```python
def run_action_script(script_path: str, working_directory: str) -> ActionResult:
    """Run an action script if it exists.

    Args:
        script_path: Path to the script (e.g., claude-chain/project/pre-action.sh)
        working_directory: Directory to run the script from

    Returns:
        ActionResult with success status, stdout, stderr
        Returns success=True if script doesn't exist (scripts are optional)

    Raises:
        ActionScriptError if script exists but fails
    """
```

**Files to modify:**
- `src/claudechain/domain/exceptions.py` - Add `ActionScriptError` exception
- `src/claudechain/domain/models.py` - Add `ActionResult` dataclass

- [ ] Phase 4: Add Pre-Action Step to GitHub Action

Add a new step in action.yml that runs the pre-action script after checkout but before Claude Code.

**Files to modify:**
- `action.yml` - Add pre-action step

**New step (after checkout, before Claude Code):**
```yaml
- name: Run pre-action script
  id: pre_action
  if: steps.prepare.outputs.has_capacity == 'true' && steps.prepare.outputs.has_task == 'true'
  shell: bash
  working-directory: ${{ inputs.working_directory }}
  env:
    PROJECT_PATH: ${{ steps.prepare.outputs.project_path }}
    ACTION_PATH: ${{ github.action_path }}
  run: |
    export PYTHONPATH="$ACTION_PATH/src:$PYTHONPATH"
    python3 -m claudechain run-action-script --type pre --project-path "$PROJECT_PATH"
```

**Files to create:**
- `src/claudechain/cli/commands/run_action_script.py` - CLI command for running action scripts

**CLI command behavior:**
- Takes `--type pre|post` and `--project-path` arguments
- Looks for `{project_path}/pre-action.sh` or `{project_path}/post-action.sh`
- Runs the script using ScriptRunner
- Exits with non-zero status if script fails (causes step to fail)
- Exits with 0 if script succeeds or doesn't exist

- [ ] Phase 5: Add Post-Action Step to GitHub Action

Add a new step that runs the post-action script after Claude Code but before finalize.

**Files to modify:**
- `action.yml` - Add post-action step after Claude Code, before finalize

**New step (after Claude Code, before finalize):**
```yaml
- name: Run post-action script
  id: post_action
  if: steps.pre_action.outcome != 'failure' && steps.parse_claude_result.outputs.success != 'false'
  shell: bash
  working-directory: ${{ inputs.working_directory }}
  env:
    PROJECT_PATH: ${{ steps.prepare.outputs.project_path }}
    ACTION_PATH: ${{ github.action_path }}
  run: |
    export PYTHONPATH="$ACTION_PATH/src:$PYTHONPATH"
    python3 -m claudechain run-action-script --type post --project-path "$PROJECT_PATH"
```

**Update finalize step condition:**
- Change `if: always() && steps.parse.outputs.skip != 'true' && steps.parse_claude_result.outputs.success != 'false'`
- To: `if: always() && steps.parse.outputs.skip != 'true' && steps.parse_claude_result.outputs.success != 'false' && steps.post_action.outcome != 'failure'`

- [ ] Phase 6: Register New CLI Command

Add the new `run-action-script` command to the CLI dispatcher.

**Files to modify:**
- `src/claudechain/cli/parser.py` - Add argument parser for run-action-script
- `src/claudechain/__main__.py` - Register command in dispatcher

**Arguments for run-action-script:**
- `--type`: Required, choices=['pre', 'post']
- `--project-path`: Required, path to project directory

- [ ] Phase 7: Add Unit Tests

Create comprehensive unit tests for the new action script functionality.

**Files to create:**
- `tests/unit/infrastructure/actions/test_script_runner.py`
- `tests/unit/cli/commands/test_run_action_script.py`

**Test cases for ScriptRunner:**
- Script doesn't exist → returns success (optional)
- Script exists and succeeds → returns success with stdout
- Script exists and fails → raises ActionScriptError
- Script with non-executable permissions → makes executable and runs
- Script produces stderr → captured in result

**Test cases for CLI command:**
- Pre-action script runs when exists
- Post-action script runs when exists
- Proper exit codes (0 for success/not-exists, non-zero for failure)
- Environment variables passed correctly

- [ ] Phase 8: Add Integration Tests

Create integration tests that verify the full flow works correctly.

**Files to create/modify:**
- `tests/integration/cli/commands/test_run_action_script.py`

**Test scenarios:**
- Full prepare → pre-action → Claude Code → post-action → finalize flow
- Pre-action failure stops execution before Claude Code
- Post-action failure stops execution before PR creation
- Missing scripts don't cause failures

- [ ] Phase 9: Validation

Verify all changes work correctly together.

**Automated tests:**
```bash
export PYTHONPATH=src:scripts
pytest tests/unit/infrastructure/actions/ -v
pytest tests/unit/cli/commands/test_run_action_script.py -v
pytest tests/integration/cli/commands/test_run_action_script.py -v
pytest tests/unit/ tests/integration/ --cov=src/claudechain --cov-report=term-missing
```

**Manual validation:**
- Create a test project with `pre-action.sh` and `post-action.sh`
- Verify pre-action runs before Claude Code
- Verify post-action runs after Claude Code
- Verify failing pre-action stops the job (no Claude Code execution)
- Verify failing post-action stops the job (no PR creation)
- Verify missing scripts don't cause failures

**Success criteria:**
- All unit and integration tests pass
- Coverage remains above 70% threshold
- Pre/post action scripts work as documented
- Failures in action scripts prevent PR creation
