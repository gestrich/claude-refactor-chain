"""Parse GitHub event and output action parameters.

This command handles event parsing for the simplified workflow, where users
pass the GitHub event context directly to the action. It parses the event,
determines if execution should be skipped, and outputs the appropriate
parameters for subsequent steps.
"""

import os
from typing import Optional

from claudechain.domain.github_event import GitHubEventContext
from claudechain.infrastructure.github.actions import GitHubActionsHelper
from claudechain.infrastructure.github.operations import compare_commits
from claudechain.services.core.project_service import ProjectService


def cmd_parse_event(
    gh: GitHubActionsHelper,
    event_name: str,
    event_json: str,
    project_name: Optional[str] = None,
    default_base_branch: Optional[str] = None,
    repo: Optional[str] = None,
) -> int:
    """Parse GitHub event and output action parameters.

    This command is invoked by the action.yml to handle the simplified workflow.
    It parses the GitHub event payload and determines:
    - Whether execution should be skipped (and why)
    - The git ref to checkout
    - The project name (from changed spec.md files or workflow_dispatch input)
    - The base branch for PR creation
    - The merged PR number (for pull_request events)

    Args:
        gh: GitHubActionsHelper for writing outputs
        event_name: GitHub event name (e.g., "pull_request", "push", "workflow_dispatch")
        event_json: JSON payload from ${{ toJson(github.event) }}
        project_name: Optional project name override (for workflow_dispatch)
        default_base_branch: Default base branch if not determined from event
        repo: GitHub repository (owner/name) for API calls

    Returns:
        0 on success, 1 on error

    Outputs (via GITHUB_OUTPUT):
        skip: "true" or "false"
        skip_reason: Reason for skipping (if skip is true)
        checkout_ref: Git ref to checkout
        project_name: Resolved project name
        base_branch: Base branch for PR creation
        merged_pr_number: PR number (for pull_request events)
    """
    try:
        print("=== ClaudeChain Event Parsing ===")
        print(f"Event name: {event_name}")
        print(f"Project name override: {project_name or '(none)'}")
        print(f"Default base branch: {default_base_branch}")

        # Parse the event
        context = GitHubEventContext.from_json(event_name, event_json)
        print(f"\nParsed event context:")
        print(f"  Event type: {context.event_name}")
        if context.pr_number:
            print(f"  PR number: {context.pr_number}")
            print(f"  PR merged: {context.pr_merged}")
            print(f"  PR labels: {context.pr_labels}")
        if context.head_ref:
            print(f"  Head ref: {context.head_ref}")
        if context.base_ref:
            print(f"  Base ref: {context.base_ref}")
        if context.ref_name:
            print(f"  Ref name: {context.ref_name}")

        # Resolve project name based on event type (mutually exclusive branches)
        resolved_project: Optional[str] = None

        if context.event_name == "workflow_dispatch":
            # workflow_dispatch: project_name is required from input
            if not project_name:
                error_msg = "workflow_dispatch requires project_name input"
                print(f"\n❌ {error_msg}")
                gh.set_error(error_msg)
                return 1
            resolved_project = project_name

        elif context.event_name == "pull_request":
            # PR merge: skip if not merged
            if not context.pr_merged:
                reason = "PR was closed but not merged"
                print(f"\n⏭️  Skipping: {reason}")
                gh.write_output("skip", "true")
                gh.write_output("skip_reason", reason)
                return 0

            # Detect project from changed spec.md files
            if repo:
                resolved_project, _ = _detect_project_from_changed_files(context, repo)

            if not resolved_project:
                reason = "No spec.md changes detected"
                print(f"\n⏭️  Skipping: {reason}")
                gh.write_output("skip", "true")
                gh.write_output("skip_reason", reason)
                return 0

        elif context.event_name == "push":
            # Push: detect project from changed files
            if repo:
                resolved_project, _ = _detect_project_from_changed_files(context, repo)

            if not resolved_project:
                reason = "No spec.md changes detected"
                print(f"\n⏭️  Skipping: {reason}")
                gh.write_output("skip", "true")
                gh.write_output("skip_reason", reason)
                return 0

        else:
            error_msg = f"Unsupported event type: {context.event_name}"
            print(f"\n❌ {error_msg}")
            gh.set_error(error_msg)
            return 1

        # Determine what to checkout based on the event type
        # - PR merge: checkout base_ref (branch the PR merged INTO) - this has the merged changes
        # - push: checkout ref_name (branch that was pushed to)
        # - workflow_dispatch: checkout ref_name (branch user selected)
        try:
            checkout_ref = context.get_checkout_ref()
        except ValueError as e:
            reason = f"Could not determine checkout ref: {e}"
            print(f"\n⏭️  Skipping: {reason}")
            gh.write_output("skip", "true")
            gh.write_output("skip_reason", reason)
            return 0

        # base_branch is used for PR creation target
        # Use default_base_branch if provided, otherwise same as checkout_ref
        # Note: Project config may override this (checked in prepare.py after checkout)
        base_branch = default_base_branch if default_base_branch else checkout_ref

        # Output results
        print(f"\n✓ Event parsing complete")
        print(f"  Skip: false")
        print(f"  Project: {resolved_project}")
        print(f"  Checkout ref: {checkout_ref}")
        print(f"  Base branch: {base_branch}")

        gh.write_output("skip", "false")
        gh.write_output("project_name", resolved_project)
        gh.write_output("checkout_ref", checkout_ref)
        gh.write_output("base_branch", base_branch)

        # For pull_request events, output the merge target branch and PR number
        # The merge target is the branch the PR was merged INTO (base_ref)
        if context.event_name == "pull_request" and context.base_ref:
            print(f"  Merge target branch: {context.base_ref}")
            gh.write_output("merge_target_branch", context.base_ref)

        if context.pr_number:
            print(f"  Merged PR number: {context.pr_number}")
            gh.write_output("merged_pr_number", str(context.pr_number))

        return 0

    except Exception as e:
        error_msg = f"Event parsing failed: {e}"
        print(f"\n❌ {error_msg}")
        gh.set_error(error_msg)
        return 1


def main() -> int:
    """Entry point for parse-event command.

    Reads parameters from environment variables:
        EVENT_NAME: GitHub event name
        EVENT_JSON: GitHub event JSON payload
        PROJECT_NAME: Optional project name override
        DEFAULT_BASE_BRANCH: Optional base branch override (if not set, derived from event)
        GITHUB_REPOSITORY: GitHub repository (owner/name) for API calls
    """
    gh = GitHubActionsHelper()

    event_name = os.environ.get("EVENT_NAME", "")
    event_json = os.environ.get("EVENT_JSON", "{}")
    project_name = os.environ.get("PROJECT_NAME", "") or None
    default_base_branch = os.environ.get("DEFAULT_BASE_BRANCH", "") or None
    repo = os.environ.get("GITHUB_REPOSITORY", "") or None

    return cmd_parse_event(
        gh=gh,
        event_name=event_name,
        event_json=event_json,
        project_name=project_name,
        default_base_branch=default_base_branch,
        repo=repo,
    )


if __name__ == "__main__":
    import sys
    sys.exit(main())


# --- Private helper functions ---


def _detect_project_from_changed_files(
    context: GitHubEventContext,
    repo: str,
) -> tuple[Optional[str], bool]:
    """Detect project from changed spec.md files.

    Works for both PR merge events (comparing base..head branches) and push events
    (comparing before..after SHAs). This enables the "changed files" triggering model
    where spec.md changes automatically trigger ClaudeChain.

    Args:
        context: Parsed GitHub event context (must have changed files context)
        repo: GitHub repository (owner/name) for API calls

    Returns:
        Tuple of (project_name, detected_from_spec_change)
        - project_name: Detected project name, or None if not detected
        - detected_from_spec_change: True if project was detected from spec.md changes
    """
    changed_files_context = context.get_changed_files_context()
    if not changed_files_context:
        return None, False

    base_ref, head_ref = changed_files_context

    # Format refs for display (truncate SHAs for push events)
    base_display = base_ref[:8] if len(base_ref) == 40 else base_ref
    head_display = head_ref[:8] if len(head_ref) == 40 else head_ref

    print(f"\n  Detecting project from changed files...")
    print(f"  Comparing {base_display}...{head_display}")

    try:
        changed_files = compare_commits(repo, base_ref, head_ref)
        print(f"  Found {len(changed_files)} changed files")
        projects = ProjectService.detect_projects_from_merge(changed_files)
        if projects:
            # For now, take the first project (Phase 4 will handle multiple)
            project_name = projects[0].name
            print(f"  Detected project from spec.md changes: {project_name}")
            if len(projects) > 1:
                print(f"  Note: Multiple projects detected ({[p.name for p in projects]}), processing first one")
            return project_name, True
    except Exception as e:
        # Compare API may fail if branch was deleted after merge
        print(f"  Could not detect from changed files: {e}")

    return None, False
