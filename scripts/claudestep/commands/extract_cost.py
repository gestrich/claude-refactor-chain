"""
Extract cost information from Claude Code action output in workflow logs.
"""

import os
import re
import subprocess
import sys
from typing import Optional


def cmd_extract_cost(args, gh):
    """
    Extract cost from a Claude Code action step in the current workflow run.

    Reads from environment:
    - GITHUB_REPOSITORY: Repository in format owner/repo
    - GITHUB_RUN_ID: Current workflow run ID
    - STEP_NAME: Name of the step to extract cost from

    Outputs:
    - cost_usd: The total cost in USD (or "0" if not found)
    """
    # Get required environment variables
    repo = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    step_name = os.environ.get("STEP_NAME", "")

    if not repo:
        gh.set_error("GITHUB_REPOSITORY environment variable is required")
        return 1

    if not run_id:
        gh.set_error("GITHUB_RUN_ID environment variable is required")
        return 1

    if not step_name:
        gh.set_error("STEP_NAME environment variable is required")
        return 1

    try:
        # Fetch workflow run logs
        print(f"Fetching logs for step '{step_name}' from run {run_id}...")
        result = subprocess.run(
            ["gh", "run", "view", run_id, "--repo", repo, "--log"],
            capture_output=True,
            text=True,
            check=True
        )

        logs = result.stdout

        # Extract cost from logs
        cost = extract_cost_from_logs(logs, step_name)

        if cost is None:
            print(f"::warning::Could not find cost information for step '{step_name}'")
            gh.write_output("cost_usd", "0")
            return 0

        # Output the cost
        gh.write_output("cost_usd", f"{cost:.6f}")
        print(f"✅ Extracted cost: ${cost:.6f} USD")

        return 0

    except subprocess.CalledProcessError as e:
        gh.set_error(f"Failed to fetch workflow logs: {e.stderr}")
        return 1
    except Exception as e:
        gh.set_error(f"Error extracting cost: {str(e)}")
        return 1


def extract_cost_from_logs(logs: str, step_name: str) -> Optional[float]:
    """
    Parse workflow logs to find the total_cost_usd value.

    Since Claude Code action runs appear in the logs under the main workflow step,
    we need to find cost entries and distinguish between main task and PR summary.

    Strategy:
    - Search for "total_cost_usd" pattern
    - For "Run Claude Code": Return the FIRST occurrence (main task)
    - For "Generate and post PR summary": Return the SECOND occurrence (if it exists)

    Args:
        logs: Complete workflow run logs
        step_name: Name of the step to find cost for (for identification purposes)

    Returns:
        Cost in USD as float, or None if not found
    """
    # Find all cost entries in the logs
    cost_pattern = re.compile(r'"total_cost_usd":\s*([\d.]+)')
    costs = []

    for line in logs.split('\n'):
        match = cost_pattern.search(line)
        if match:
            try:
                cost = float(match.group(1))
                costs.append(cost)
            except ValueError:
                continue

    # Now determine which cost to return based on the step name
    if not costs:
        return None

    # If this is for the main Claude Code run, return the first cost
    if 'Run Claude Code' in step_name or 'Claude Code' in step_name:
        return costs[0] if costs else None

    # If this is for the PR summary, return the second cost
    if 'summary' in step_name.lower() or 'Summary' in step_name:
        return costs[1] if len(costs) > 1 else None

    # Default: return the first cost
    return costs[0] if costs else None
