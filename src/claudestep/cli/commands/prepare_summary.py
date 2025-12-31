"""Prepare summary command - generate prompt for PR summary"""

import argparse
import os

from claudestep.infrastructure.github.actions import GitHubActionsHelper
from claudestep.cli.commands.extract_cost import extract_cost_from_execution
import json


def cmd_prepare_summary(args: argparse.Namespace, gh: GitHubActionsHelper) -> int:
    """Handle 'prepare-summary' subcommand - generate prompt for PR summary comment

    This command reads environment variables and generates a prompt for Claude Code
    to analyze a PR diff and post a summary comment. It also extracts cost information
    from both the main task execution and any previous summary generation.

    Args:
        args: Parsed command-line arguments
        gh: GitHub Actions helper instance

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Read environment variables
        pr_number = os.environ.get("PR_NUMBER", "")
        task = os.environ.get("TASK", "")
        repo = os.environ.get("GITHUB_REPOSITORY", "")
        run_id = os.environ.get("GITHUB_RUN_ID", "")
        action_path = os.environ.get("ACTION_PATH", "")
        main_execution_file = os.environ.get("MAIN_EXECUTION_FILE", "")
        summary_execution_file = os.environ.get("SUMMARY_EXECUTION_FILE", "")

        # Validate required inputs
        if not pr_number:
            gh.set_notice("No PR number provided, skipping summary generation")
            return 0  # Not an error, just skip

        if not task:
            gh.set_error("TASK environment variable is required")
            return 1

        if not repo or not run_id:
            gh.set_error("GITHUB_REPOSITORY and GITHUB_RUN_ID are required")
            return 1

        # Construct workflow URL
        workflow_url = f"https://github.com/{repo}/actions/runs/{run_id}"

        # Load prompt template
        # Use new resources path in src/claudestep/resources/prompts/
        template_path = os.path.join(action_path, "src/claudestep/resources/prompts/summary_prompt.md")

        try:
            with open(template_path, "r") as f:
                template = f.read()
        except FileNotFoundError:
            gh.set_error(f"Prompt template not found: {template_path}")
            return 1

        # Substitute variables in template
        summary_prompt = template.replace("{TASK_DESCRIPTION}", task)
        summary_prompt = summary_prompt.replace("{PR_NUMBER}", pr_number)
        summary_prompt = summary_prompt.replace("{WORKFLOW_URL}", workflow_url)

        # Write output
        gh.write_output("summary_prompt", summary_prompt)

        print(f"✅ Summary prompt prepared for PR #{pr_number}")
        print(f"   Task: {task}")
        print(f"   Prompt length: {len(summary_prompt)} characters")

        # Extract costs from execution files
        main_cost = _extract_cost_from_file(main_execution_file, "main task")
        summary_cost = _extract_cost_from_file(summary_execution_file, "summary generation")
        total_cost = main_cost + summary_cost

        # Output cost values
        gh.write_output("main_cost", f"{main_cost:.6f}")
        gh.write_output("summary_cost", f"{summary_cost:.6f}")
        gh.write_output("total_cost", f"{total_cost:.6f}")

        print(f"💰 Cost extraction:")
        print(f"   Main task: ${main_cost:.6f} USD")
        print(f"   Summary generation: ${summary_cost:.6f} USD")
        print(f"   Total: ${total_cost:.6f} USD")

        return 0

    except Exception as e:
        gh.set_error(f"Failed to prepare summary: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


def _extract_cost_from_file(execution_file: str, context: str) -> float:
    """Extract cost from a Claude Code execution file.

    Args:
        execution_file: Path to the execution file
        context: Description of what this cost is for (for logging)

    Returns:
        Cost in USD as float, or 0.0 if not found/error
    """
    if not execution_file or not execution_file.strip():
        print(f"   No execution file for {context}, cost = $0.00")
        return 0.0

    if not os.path.exists(execution_file):
        print(f"   Execution file not found for {context}: {execution_file}, cost = $0.00")
        return 0.0

    try:
        with open(execution_file, 'r') as f:
            data = json.load(f)

        # Handle list format (may have multiple executions)
        if isinstance(data, list):
            # Filter to only items that have cost information
            items_with_cost = [item for item in data if isinstance(item, dict) and 'total_cost_usd' in item]

            if items_with_cost:
                # Use the last item with cost
                data = items_with_cost[-1]
            elif data:
                # Fallback to last item
                data = data[-1]
            else:
                print(f"   Empty execution data for {context}, cost = $0.00")
                return 0.0

        # Extract cost
        cost = extract_cost_from_execution(data)
        if cost is None:
            print(f"   Could not find cost in execution file for {context}, cost = $0.00")
            return 0.0

        return cost

    except json.JSONDecodeError as e:
        print(f"   Failed to parse execution file for {context}: {str(e)}, cost = $0.00")
        return 0.0
    except Exception as e:
        print(f"   Error extracting cost for {context}: {str(e)}, cost = $0.00")
        return 0.0
