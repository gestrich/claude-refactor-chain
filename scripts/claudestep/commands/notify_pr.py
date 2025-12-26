"""
Generate Slack notification message for created PR.
"""

import os


def cmd_notify_pr(args, gh):
    """
    Generate Slack notification message for a created PR.

    Reads from environment:
    - PR_NUMBER: Pull request number
    - PR_URL: Pull request URL
    - PROJECT_NAME: Name of the project
    - TASK: Task description
    - MAIN_COST: Cost of main refactoring task (USD)
    - SUMMARY_COST: Cost of PR summary generation (USD)
    - GITHUB_REPOSITORY: Repository in format owner/repo

    Outputs:
    - slack_message: Formatted Slack message in mrkdwn format
    - has_pr: "true" if PR was created
    """
    # Get required environment variables
    pr_number = os.environ.get("PR_NUMBER", "").strip()
    pr_url = os.environ.get("PR_URL", "").strip()
    project_name = os.environ.get("PROJECT_NAME", "").strip()
    task = os.environ.get("TASK", "").strip()
    main_cost = os.environ.get("MAIN_COST", "0").strip()
    summary_cost = os.environ.get("SUMMARY_COST", "0").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "")

    # If no PR, don't send notification
    if not pr_number or not pr_url:
        gh.write_output("has_pr", "false")
        print("No PR created, skipping Slack notification")
        return 0

    try:
        # Parse costs
        try:
            main_cost_val = float(main_cost)
        except ValueError:
            main_cost_val = 0.0

        try:
            summary_cost_val = float(summary_cost)
        except ValueError:
            summary_cost_val = 0.0

        total_cost = main_cost_val + summary_cost_val

        # Format the Slack message
        message = format_pr_notification(
            pr_number=pr_number,
            pr_url=pr_url,
            project_name=project_name,
            task=task,
            main_cost=main_cost_val,
            summary_cost=summary_cost_val,
            total_cost=total_cost,
            repo=repo
        )

        # Output for Slack
        gh.write_output("slack_message", message)
        gh.write_output("has_pr", "true")

        print("=== Slack Notification Message ===")
        print(message)
        print()

        return 0

    except Exception as e:
        gh.set_error(f"Error generating PR notification: {str(e)}")
        gh.write_output("has_pr", "false")
        return 1


def format_pr_notification(
    pr_number: str,
    pr_url: str,
    project_name: str,
    task: str,
    main_cost: float,
    summary_cost: float,
    total_cost: float,
    repo: str
) -> str:
    """
    Format PR notification for Slack in mrkdwn format.

    Args:
        pr_number: PR number
        pr_url: PR URL
        project_name: Project name
        task: Task description
        main_cost: Main task cost in USD
        summary_cost: PR summary cost in USD
        total_cost: Total cost in USD
        repo: Repository name

    Returns:
        Formatted Slack message in mrkdwn
    """
    # Build the message with Slack mrkdwn formatting
    lines = [
        f"🎉 *New PR Created*",
        "",
        f"*PR:* <{pr_url}|#{pr_number}>",
        f"*Project:* `{project_name}`",
        f"*Task:* {task}",
        "",
        "*💰 Cost Breakdown:*",
        f"```",
        f"Main task:      ${main_cost:.6f}",
        f"PR summary:     ${summary_cost:.6f}",
        f"─────────────────────────────",
        f"Total:          ${total_cost:.6f}",
        f"```",
    ]

    return "\n".join(lines)
