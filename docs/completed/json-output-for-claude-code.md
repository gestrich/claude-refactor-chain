## Background

Currently, ClaudeChain uses the `anthropics/claude-code-action@v1` action to run Claude Code for both the main task and the PR summary. The action already supports passing CLI arguments via `claude_args`, including `--output-format json` and `--json-schema`.

By adding JSON output arguments, we can:
- Get structured success/error indicators from Claude Code runs
- Parse the output reliably from the execution file
- Fail the action and skip PR creation when errors occur
- Post detailed error information to Slack

## Phases

- [x] Phase 1: Define JSON schemas for Claude Code outputs

Create JSON schemas for both execution types:
- **Main task schema**: `success` (boolean), `error_message` (optional string), `summary` (string describing what was done)
- **Summary task schema**: `success` (boolean), `error_message` (optional string), `summary_content` (the PR summary text)

Add schema definitions to a new file `src/claudechain/domain/claude_schemas.py` containing the schema dictionaries as Python constants that can be serialized to JSON for the CLI args.

- [x] Phase 2: Update prepare.py to output JSON schema

Update `src/claudechain/cli/commands/prepare.py` to:
- Output the main task JSON schema as a step output (escaped for shell)
- The schema will be passed to `claude_args` in action.yml

- [x] Phase 3: Update action.yml to pass JSON output args

Modify the "Run Claude Code" step:
- Add `--output-format json --json-schema '${{ steps.prepare.outputs.json_schema }}'` to `claude_args`
- The execution file will contain structured JSON output

Modify the "Generate PR summary" step similarly with the summary schema.

- [x] Phase 4: Parse JSON output and gate PR creation

Create a new step after "Run Claude Code" to parse the execution file:
- Read the JSON execution file
- Extract `structured_output` from the last element (when using `--verbose`)
- Check `success` field
- Set outputs: `claude_success`, `claude_error`

Update finalize step condition:
- Only run if `steps.parse_result.outputs.success == 'true'`
- If failed, skip PR creation entirely

- [x] Phase 5: Add Slack error notification

Add error notification formatting to `src/claudechain/domain/formatters/slack_block_kit_formatter.py`:
- Add `format_error_notification()` method
- Include project name, task description, error message, and link to action run

Add new step in `action.yml`:
- "Post error to Slack" runs when main task failed
- Condition: `if: steps.parse_result.outputs.success == 'false' && inputs.slack_webhook_url != ''`
- Use error-styled Slack payload

- [x] Phase 6: Add tests

Write tests for:
- `tests/unit/domain/test_claude_schemas.py` - Schema structure validation
- `tests/unit/domain/formatters/test_slack_block_kit_formatter.py` - Error notification format

- [x] Phase 7: Validation

Run the test suite:
```bash
export PYTHONPATH=src:scripts
pytest tests/unit/ tests/integration/ -v --cov=src/claudechain --cov-report=term-missing
```

Verify:
- All tests pass
- Coverage meets threshold
- Schema definitions are valid JSON Schema
