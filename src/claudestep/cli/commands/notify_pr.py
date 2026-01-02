"""
Generate Slack notification message for created PR.
"""

import json

from claudestep.infrastructure.github.actions import GitHubActionsHelper


def cmd_notify_pr(
    gh: GitHubActionsHelper,
    pr_number: str,
    pr_url: str,
    project_name: str,
    task: str,
    main_cost: str,
    summary_cost: str,
    model_breakdown_json: str,
    repo: str,
) -> int:
    """
    Generate Slack notification message for a created PR.

    All parameters passed explicitly, no environment variable access.

    Args:
        gh: GitHub Actions helper for outputs and errors
        pr_number: Pull request number
        pr_url: Pull request URL
        project_name: Name of the project
        task: Task description
        main_cost: Cost of main refactoring task (USD) as string
        summary_cost: Cost of PR summary generation (USD) as string
        model_breakdown_json: JSON string with per-model cost breakdown
        repo: Repository in format owner/repo

    Outputs:
        slack_message: Formatted Slack message in mrkdwn format
        has_pr: "true" if PR was created

    Returns:
        0 on success, 1 on error
    """
    # Strip whitespace from inputs
    pr_number = pr_number.strip()
    pr_url = pr_url.strip()
    project_name = project_name.strip()
    task = task.strip()
    main_cost = main_cost.strip()
    summary_cost = summary_cost.strip()
    model_breakdown_json = model_breakdown_json.strip()

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

        # Parse model breakdown
        model_breakdown = []
        if model_breakdown_json:
            try:
                model_breakdown = json.loads(model_breakdown_json)
            except json.JSONDecodeError:
                pass

        # Format the Slack message
        message = format_pr_notification(
            pr_number=pr_number,
            pr_url=pr_url,
            project_name=project_name,
            task=task,
            main_cost=main_cost_val,
            summary_cost=summary_cost_val,
            total_cost=total_cost,
            model_breakdown=model_breakdown,
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
    model_breakdown: list[dict],
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
        model_breakdown: List of dicts with per-model cost data
        repo: Repository name

    Returns:
        Formatted Slack message in mrkdwn
    """
    # Build the message with Slack mrkdwn formatting
    lines = [
        "🎉 *New PR Created*",
        "",
        f"*PR:* <{pr_url}|#{pr_number}>",
        f"*Project:* `{project_name}`",
        f"*Task:* {task}",
        "",
        "*💰 Cost Breakdown:*",
        "```",
        f"Main task:      ${main_cost:.6f}",
        f"PR summary:     ${summary_cost:.6f}",
        "─────────────────────────────",
        f"Total:          ${total_cost:.6f}",
        "```",
    ]

    # Add per-model breakdown if available
    if model_breakdown:
        lines.append("")
        lines.append("*📊 Per-Model Usage:*")
        lines.append("```")
        for model in model_breakdown:
            model_name = model.get("model", "unknown")
            cost = model.get("cost", 0.0)
            input_tokens = model.get("input_tokens", 0)
            output_tokens = model.get("output_tokens", 0)
            # Truncate long model names for display
            display_name = model_name[:30] if len(model_name) > 30 else model_name
            lines.append(f"{display_name}")
            lines.append(f"  Cost: ${cost:.6f} | In: {input_tokens:,} | Out: {output_tokens:,}")
        lines.append("```")

    return "\n".join(lines)
