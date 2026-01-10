"""JSON schemas for Claude Code structured output.

These schemas define the expected output format from Claude Code runs.
Claude Code supports `--output-format json --json-schema <schema>` arguments
to get structured, parseable responses.

Usage in action.yml:
    claude_args: '--output-format json --json-schema "${{ steps.prepare.outputs.json_schema }}"'

Reference: https://docs.anthropic.com/en/docs/claude-code
"""

import json
from typing import Any


# JSON Schema for main task execution
# Claude should output this when completing a task from spec.md
MAIN_TASK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "success": {
            "type": "boolean",
            "description": "Whether the task was completed successfully"
        },
        "error_message": {
            "type": "string",
            "description": "Error message if the task failed (only present when success is false)"
        },
        "summary": {
            "type": "string",
            "description": "Brief summary of what was done to complete the task"
        }
    },
    "required": ["success", "summary"],
    "additionalProperties": False
}

# JSON Schema for PR summary generation
# Claude should output this when generating a PR summary
SUMMARY_TASK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "success": {
            "type": "boolean",
            "description": "Whether the summary was generated successfully"
        },
        "error_message": {
            "type": "string",
            "description": "Error message if summary generation failed (only present when success is false)"
        },
        "summary_content": {
            "type": "string",
            "description": "The generated PR summary text in markdown format"
        }
    },
    "required": ["success", "summary_content"],
    "additionalProperties": False
}


def get_main_task_schema_json() -> str:
    """Get the main task schema as a JSON string for CLI args.

    Returns:
        JSON string suitable for passing to --json-schema argument
    """
    return json.dumps(MAIN_TASK_SCHEMA, separators=(",", ":"))


def get_summary_task_schema_json() -> str:
    """Get the summary task schema as a JSON string for CLI args.

    Returns:
        JSON string suitable for passing to --json-schema argument
    """
    return json.dumps(SUMMARY_TASK_SCHEMA, separators=(",", ":"))
