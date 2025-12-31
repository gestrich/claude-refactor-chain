"""Migration helper command for transitioning from index-based to hash-based PRs.

This command detects old index-based PRs and provides guidance for migrating
to the new hash-based format.
"""

import os
import sys

from claudestep.services.core.pr_service import PRService
from claudestep.services.core.task_service import TaskService
from claudestep.services.core.project_service import ProjectService
from claudestep.domain.project import Project
from claudestep.infrastructure.github.actions import GitHubActionsHelper


def run_migrate_to_hashes(args) -> int:
    """Detect old index-based PRs and provide migration guidance.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Get GitHub repository
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        print("Error: GITHUB_REPOSITORY environment variable not set")
        print("This command must be run in a GitHub Actions workflow")
        return 1

    # Get project name from args
    project_name = args.project
    label = args.label or "claudestep"

    print(f"=== ClaudeStep Migration Helper ===")
    print(f"Repository: {repo}")
    print(f"Project: {project_name}")
    print()

    # Initialize services
    pr_service = PRService(repo)
    task_service = TaskService(repo, pr_service)
    project_service = ProjectService(repo, pr_service)

    # Detect project if not specified
    if not project_name:
        print("Detecting project from open PRs...")
        detected_project = project_service.detect_project_from_pr(label)
        if not detected_project:
            print("Error: No project detected. Please specify --project")
            return 1
        project_name = detected_project
        print(f"✅ Detected project: {project_name}")
        print()

    # Get all open PRs for this project
    print(f"Scanning open PRs for project '{project_name}'...")
    open_prs = pr_service.get_open_prs_for_project(project_name, label=label)

    if not open_prs:
        print(f"✅ No open PRs found for project '{project_name}'")
        print("Nothing to migrate.")
        return 0

    # Categorize PRs by format
    index_based_prs = []
    hash_based_prs = []

    for pr in open_prs:
        if pr.task_index is not None:
            index_based_prs.append(pr)
        elif pr.task_hash is not None:
            hash_based_prs.append(pr)

    # Display results
    print(f"\n=== Migration Status ===")
    print(f"Total open PRs: {len(open_prs)}")
    print(f"  - Hash-based (new format): {len(hash_based_prs)}")
    print(f"  - Index-based (old format): {len(index_based_prs)}")
    print()

    if not index_based_prs:
        print("✅ All PRs are using the new hash-based format!")
        print("No migration needed.")
        return 0

    # Display migration guidance
    print("⚠️  Found index-based PRs that need migration:")
    print()

    for pr in index_based_prs:
        print(f"  PR #{pr.number}: {pr.title}")
        print(f"    Branch: {pr.head_ref_name}")
        print(f"    URL: {pr.url}")
        print(f"    Task index: {pr.task_index}")
        print()

    print("=== Migration Steps ===")
    print()
    print("1. Review each index-based PR above")
    print("2. Choose one of the following options for each PR:")
    print()
    print("   Option A: Merge the PR if it's ready")
    print("     - Review and approve the PR")
    print("     - Merge it to main")
    print("     - ClaudeStep will mark the task as complete")
    print()
    print("   Option B: Close the PR if work needs to restart")
    print("     - Close the PR on GitHub")
    print("     - ClaudeStep will automatically create a new hash-based PR")
    print("     - The new PR will have the same task but use hash-based identification")
    print()
    print("3. Wait for the next ClaudeStep run")
    print("   - New PRs will automatically use hash-based format")
    print("   - You can reorder/insert tasks in spec.md without breaking PR mapping")
    print()
    print("=== Why Migrate? ===")
    print()
    print("Hash-based identification provides:")
    print("  ✓ Stable task tracking when reordering tasks in spec.md")
    print("  ✓ Safe task insertion without breaking existing PRs")
    print("  ✓ Automatic detection of orphaned PRs (tasks that changed)")
    print()
    print("Index-based format is DEPRECATED and will be removed in ~6 months")
    print()
    print("For more information, see:")
    print("  - docs/user-guides/modifying-tasks.md")
    print("  - docs/architecture/architecture.md (Hash-Based Task Identification)")
    print()

    # GitHub Actions integration
    if os.environ.get("GITHUB_ACTIONS") == "true":
        gh = GitHubActionsHelper()
        summary = "## Migration Status\n\n"
        summary += f"**Total open PRs:** {len(open_prs)}\n"
        summary += f"- Hash-based (new): {len(hash_based_prs)}\n"
        summary += f"- Index-based (old): {len(index_based_prs)}\n\n"

        if index_based_prs:
            summary += "### ⚠️ Index-Based PRs Requiring Migration\n\n"
            for pr in index_based_prs:
                summary += f"- [PR #{pr.number}]({pr.url}): {pr.title}\n"
                summary += f"  - Branch: `{pr.head_ref_name}`\n"
                summary += f"  - Task index: {pr.task_index}\n\n"

            summary += "### Migration Options\n\n"
            summary += "1. **Merge** the PR if it's ready\n"
            summary += "2. **Close** the PR to restart with hash-based format\n\n"
            summary += "See [Migration Guide](docs/user-guides/modifying-tasks.md) for details.\n"
        else:
            summary += "✅ All PRs use the new hash-based format!\n"

        gh.write_step_summary(summary)

    return 0
