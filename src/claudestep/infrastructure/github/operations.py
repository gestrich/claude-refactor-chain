"""GitHub CLI and API operations"""

import base64
import json
import os
import subprocess
import tempfile
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional

from claudestep.domain.exceptions import GitHubAPIError
from claudestep.domain.github_models import GitHubPullRequest
from claudestep.infrastructure.git.operations import run_command
from claudestep.infrastructure.github.actions import GitHubActionsHelper


def run_gh_command(args: List[str]) -> str:
    """Run a GitHub CLI command and return stdout

    Args:
        args: gh command arguments (without 'gh' prefix)

    Returns:
        Command stdout as string

    Raises:
        GitHubAPIError: If gh command fails
    """
    try:
        result = run_command(["gh"] + args)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise GitHubAPIError(f"GitHub CLI command failed: {' '.join(args)}\n{e.stderr}")


def gh_api_call(endpoint: str, method: str = "GET") -> Dict[str, Any]:
    """Call GitHub REST API using gh CLI

    Args:
        endpoint: API endpoint path (e.g., "/repos/owner/repo/actions/runs")
        method: HTTP method (GET, POST, etc.)

    Returns:
        Parsed JSON response

    Raises:
        GitHubAPIError: If API call fails
    """
    try:
        output = run_gh_command(["api", endpoint, "--method", method])
        return json.loads(output) if output else {}
    except json.JSONDecodeError as e:
        raise GitHubAPIError(f"Invalid JSON from API: {str(e)}")


def download_artifact_json(repo: str, artifact_id: int) -> Optional[Dict[str, Any]]:
    """Download and parse artifact JSON using GitHub API

    Args:
        repo: GitHub repository (owner/name)
        artifact_id: Artifact ID to download

    Returns:
        Parsed JSON content or None if download fails
    """
    try:
        # Get artifact download URL (returns a redirect)
        download_endpoint = f"/repos/{repo}/actions/artifacts/{artifact_id}/zip"

        # Create temp file for the zip
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            tmp_zip_path = tmp_file.name

        try:
            # Download the zip file using gh api
            # The endpoint returns a redirect which gh api should follow
            subprocess.run(
                ["gh", "api", download_endpoint, "--method", "GET"],
                stdout=open(tmp_zip_path, 'wb'),
                stderr=subprocess.PIPE,
                check=True
            )

            # Extract and parse the JSON from the zip
            with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
                # Get the first JSON file in the zip
                json_files = [f for f in zip_ref.namelist() if f.endswith('.json')]
                if json_files:
                    with zip_ref.open(json_files[0]) as json_file:
                        return json.load(json_file)
                else:
                    print(f"Warning: No JSON file found in artifact {artifact_id}")
                    return None

        finally:
            # Clean up temp file
            if os.path.exists(tmp_zip_path):
                os.remove(tmp_zip_path)

    except Exception as e:
        print(f"Warning: Failed to download/parse artifact {artifact_id}: {e}")
        return None


def ensure_label_exists(label: str, gh: GitHubActionsHelper) -> None:
    """Ensure a GitHub label exists in the repository, create if it doesn't

    Args:
        label: Label name to ensure exists
        gh: GitHub Actions helper instance for logging
    """
    try:
        # Try to create the label
        # If it already exists, gh will return an error which we'll catch
        run_gh_command([
            "label", "create", label,
            "--description", "ClaudeStep automated refactoring",
            "--color", "0E8A16"  # Green color for refactor labels
        ])
        gh.write_step_summary(f"- Label '{label}': ✅ Created")
        gh.set_notice(f"Created label '{label}'")
    except GitHubAPIError as e:
        # Check if error is because label already exists
        if "already exists" in str(e).lower():
            gh.write_step_summary(f"- Label '{label}': ✅ Already exists")
        else:
            # Re-raise if it's a different error
            raise


def get_file_from_branch(repo: str, branch: str, file_path: str) -> Optional[str]:
    """Fetch file content from a specific branch via GitHub API

    Args:
        repo: GitHub repository in format "owner/repo"
        branch: Branch name to fetch from
        file_path: Path to file within repository

    Returns:
        File content as string, or None if file not found

    Raises:
        GitHubAPIError: If API call fails for reasons other than file not found
    """
    endpoint = f"/repos/{repo}/contents/{file_path}?ref={branch}"

    try:
        response = gh_api_call(endpoint, method="GET")

        # GitHub API returns content as Base64 encoded
        if "content" in response:
            # Remove newlines that GitHub adds to the base64 string
            encoded_content = response["content"].replace("\n", "")
            decoded_content = base64.b64decode(encoded_content).decode("utf-8")
            return decoded_content
        else:
            return None

    except GitHubAPIError as e:
        # If it's a 404 (file not found), return None
        if "404" in str(e) or "Not Found" in str(e):
            return None
        # Re-raise other errors
        raise


def file_exists_in_branch(repo: str, branch: str, file_path: str) -> bool:
    """Check if a file exists in a specific branch

    Args:
        repo: GitHub repository in format "owner/repo"
        branch: Branch name to check
        file_path: Path to file within repository

    Returns:
        True if file exists, False otherwise
    """
    content = get_file_from_branch(repo, branch, file_path)
    return content is not None


def list_pull_requests(
    repo: str,
    state: str = "all",
    label: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 100
) -> List[GitHubPullRequest]:
    """Fetch PRs with filtering, returns domain models

    This function provides GitHub PR querying capabilities for future use cases
    such as synchronization commands. It encapsulates all GitHub CLI command
    construction and JSON parsing, returning type-safe domain models.

    Args:
        repo: GitHub repository (owner/name)
        state: "open", "closed", "merged", or "all"
        label: Optional label filter
        since: Optional date filter (for created_at)
        limit: Max results (default 100)

    Returns:
        List of GitHubPullRequest domain models

    Raises:
        GitHubAPIError: If gh command fails

    Example:
        >>> prs = list_pull_requests("owner/repo", state="merged", label="claudestep")
        >>> for pr in prs:
        ...     print(f"PR #{pr.number}: {pr.title}")
    """
    # Build gh pr list command
    args = [
        "pr", "list",
        "--repo", repo,
        "--state", state,
        "--limit", str(limit),
        "--json", "number,title,state,createdAt,mergedAt,assignees,labels"
    ]

    # Add label filter if specified
    if label:
        args.extend(["--label", label])

    # Execute command and parse JSON
    try:
        output = run_gh_command(args)
        pr_data = json.loads(output) if output else []
    except json.JSONDecodeError as e:
        raise GitHubAPIError(f"Invalid JSON from gh pr list: {str(e)}")

    # Parse into domain models
    prs = [GitHubPullRequest.from_dict(pr) for pr in pr_data]

    # Apply date filter if specified (gh pr list doesn't support --since)
    if since:
        prs = [pr for pr in prs if pr.created_at >= since]

    return prs


def list_merged_pull_requests(
    repo: str,
    since: datetime,
    label: Optional[str] = None,
    limit: int = 100
) -> List[GitHubPullRequest]:
    """Convenience function for fetching merged PRs

    Filters by merged state and date range. Useful for collecting statistics
    or synchronizing metadata.

    Args:
        repo: GitHub repository (owner/name)
        since: Only include PRs merged on or after this date
        label: Optional label filter
        limit: Max results (default 100)

    Returns:
        List of merged GitHubPullRequest domain models

    Example:
        >>> from datetime import datetime, timedelta, timezone
        >>> cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        >>> recent_merged = list_merged_pull_requests("owner/repo", since=cutoff)
    """
    # Get merged PRs
    prs = list_pull_requests(repo, state="merged", label=label, limit=limit)

    # Filter by merged_at date (not just created_at)
    # Since gh pr list doesn't support date filtering, we do it post-fetch
    filtered = [pr for pr in prs if pr.merged_at and pr.merged_at >= since]

    return filtered


def list_open_pull_requests(
    repo: str,
    label: Optional[str] = None,
    limit: int = 100
) -> List[GitHubPullRequest]:
    """Convenience function for fetching open PRs

    Useful for checking reviewer workload or finding stale PRs.

    Args:
        repo: GitHub repository (owner/name)
        label: Optional label filter
        limit: Max results (default 100)

    Returns:
        List of open GitHubPullRequest domain models

    Example:
        >>> open_prs = list_open_pull_requests("owner/repo", label="claudestep")
        >>> print(f"Found {len(open_prs)} open ClaudeStep PRs")
    """
    return list_pull_requests(repo, state="open", label=label, limit=limit)
