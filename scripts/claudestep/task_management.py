"""Task finding, marking, and tracking operations"""

import json
import os
import re
from typing import Optional

from claudestep.exceptions import FileNotFoundError, GitHubAPIError
from claudestep.github_operations import gh_api_call, run_gh_command


def generate_task_id(task: str, max_length: int = 30) -> str:
    """Generate sanitized task ID from task description

    Args:
        task: Task description text
        max_length: Maximum length for the ID

    Returns:
        Sanitized task ID (lowercase, alphanumeric + dashes, truncated)
    """
    # Convert to lowercase and replace non-alphanumeric with dashes
    sanitized = re.sub(r"[^a-z0-9]+", "-", task.lower())
    # Remove leading/trailing dashes
    sanitized = sanitized.strip("-")
    # Truncate to max length and remove trailing dash if present
    sanitized = sanitized[:max_length].rstrip("-")
    return sanitized


def find_next_available_task(plan_file: str, skip_indices: Optional[set] = None) -> Optional[tuple]:
    """Find first unchecked task not in skip_indices

    Args:
        plan_file: Path to spec.md file
        skip_indices: Set of task indices to skip (in-progress tasks)

    Returns:
        Tuple of (task_index, task_text) or None if no available task found
        task_index is 1-based position in spec.md

    Raises:
        FileNotFoundError: If spec file doesn't exist
    """
    if skip_indices is None:
        skip_indices = set()

    if not os.path.exists(plan_file):
        raise FileNotFoundError(f"Spec file not found: {plan_file}")

    with open(plan_file, "r") as f:
        task_index = 1
        for line in f:
            # Check for unchecked task
            match = re.match(r'^\s*- \[ \] (.+)$', line)
            if match:
                if task_index not in skip_indices:
                    return (task_index, match.group(1).strip())
                else:
                    print(f"Skipping task {task_index} (already in progress)")
                task_index += 1
            # Also count completed tasks to maintain correct indices
            elif re.match(r'^\s*- \[[xX]\] ', line):
                task_index += 1

    return None


def mark_task_complete(plan_file: str, task: str) -> None:
    """Mark a task as complete in the spec file

    Args:
        plan_file: Path to spec.md file
        task: Task description to mark complete

    Raises:
        FileNotFoundError: If spec file doesn't exist
    """
    if not os.path.exists(plan_file):
        raise FileNotFoundError(f"Spec file not found: {plan_file}")

    with open(plan_file, "r") as f:
        content = f.read()

    # Replace the unchecked task with checked version
    # Match the task with surrounding whitespace preserved
    pattern = r'(\s*)- \[ \] ' + re.escape(task)
    replacement = r'\1- [x] ' + task
    updated_content = re.sub(pattern, replacement, content, count=1)

    with open(plan_file, "w") as f:
        f.write(updated_content)


def get_in_progress_task_indices(repo: str, label: str, project: str) -> set:
    """Get set of task indices currently being worked on

    Args:
        repo: GitHub repository (owner/name)
        label: GitHub label to filter PRs
        project: Project name to match artifacts

    Returns:
        Set of task indices that are in progress

    Raises:
        GitHubAPIError: If GitHub API calls fail
    """
    in_progress = set()

    # Use gh CLI to list PRs
    try:
        pr_output = run_gh_command([
            "pr", "list",
            "--repo", repo,
            "--label", label,
            "--state", "open",
            "--json", "number,headRefName"
        ])
        prs = json.loads(pr_output) if pr_output else []
    except (GitHubAPIError, json.JSONDecodeError) as e:
        print(f"Warning: Failed to list PRs: {e}")
        return set()

    print(f"Found {len(prs)} open PR(s) with label '{label}'")

    for pr in prs:
        branch = pr["headRefName"]
        pr_number = pr["number"]

        # First, try to extract task index from branch name as a quick check
        # Branch format: YYYY-MM-{project}-{index}
        # Example: 2025-12-test-project-abc123-1
        try:
            # Extract the last part after the final dash
            parts = branch.rsplit("-", 1)
            if len(parts) == 2:
                task_index = int(parts[1])
                in_progress.add(task_index)
                print(f"Found in-progress task {task_index} from PR #{pr_number} (branch name)")
                continue  # Skip artifact check if we got the index from branch name
        except (ValueError, IndexError):
            # Branch name doesn't match expected format, fall back to artifact check
            pass

        # Fallback: Get workflow runs for this branch and check artifacts
        try:
            api_response = gh_api_call(
                f"/repos/{repo}/actions/runs?branch={branch}&status=completed&per_page=10"
            )
            runs = api_response.get("workflow_runs", [])
        except GitHubAPIError as e:
            print(f"Warning: Failed to get runs for PR #{pr_number}: {e}")
            continue

        # Check most recent successful run
        for run in runs:
            if run.get("conclusion") == "success":
                # Get artifacts from this run
                try:
                    artifacts_data = gh_api_call(
                        f"/repos/{repo}/actions/runs/{run['id']}/artifacts"
                    )
                    artifacts = artifacts_data.get("artifacts", [])

                    for artifact in artifacts:
                        # Parse task index from artifact name
                        # Format: task-metadata-{project}-{index}.json
                        name = artifact["name"]
                        if name.startswith(f"task-metadata-{project}-"):
                            try:
                                # Extract index from name
                                suffix = name.replace(f"task-metadata-{project}-", "")
                                index_str = suffix.replace(".json", "")
                                task_index = int(index_str)
                                in_progress.add(task_index)
                                print(f"Found in-progress task {task_index} from PR #{pr_number} (artifact)")
                            except ValueError:
                                print(f"Warning: Could not parse task index from artifact name: {name}")
                                continue
                except GitHubAPIError as e:
                    print(f"Warning: Failed to get artifacts for run {run['id']}: {e}")
                    continue
                break  # Only check first successful run

    return in_progress
