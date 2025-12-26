"""
Post cost breakdown comment to a pull request.
"""

import os
import subprocess
import tempfile


def cmd_add_cost_comment(args, gh):
    """
    Post a cost breakdown comment to a PR.

    Reads from environment:
    - PR_NUMBER: Pull request number
    - MAIN_COST: Cost of main refactoring task (USD)
    - SUMMARY_COST: Cost of PR summary generation (USD)
    - GITHUB_REPOSITORY: Repository in format owner/repo
    - GITHUB_RUN_ID: Workflow run ID

    Outputs:
    - comment_posted: "true" if comment was posted, "false" otherwise
    """
    # Get required environment variables
    pr_number = os.environ.get("PR_NUMBER", "").strip()
    main_cost = os.environ.get("MAIN_COST", "0").strip()
    summary_cost = os.environ.get("SUMMARY_COST", "0").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")

    # If no PR number, skip gracefully
    if not pr_number:
        print("::notice::No PR number provided, skipping cost comment")
        gh.write_output("comment_posted", "false")
        return 0

    if not repo:
        gh.set_error("GITHUB_REPOSITORY environment variable is required")
        return 1

    if not run_id:
        gh.set_error("GITHUB_RUN_ID environment variable is required")
        return 1

    try:
        # Parse costs as floats
        try:
            main_cost_val = float(main_cost)
        except ValueError:
            main_cost_val = 0.0

        try:
            summary_cost_val = float(summary_cost)
        except ValueError:
            summary_cost_val = 0.0

        total_cost = main_cost_val + summary_cost_val

        # Format the comment
        comment = format_cost_comment(main_cost_val, summary_cost_val, total_cost, repo, run_id)

        # Write comment to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(comment)
            temp_file = f.name

        try:
            # Post comment to PR using gh CLI
            print(f"Posting cost breakdown to PR #{pr_number}...")
            subprocess.run(
                ["gh", "pr", "comment", pr_number, "--body-file", temp_file],
                check=True,
                capture_output=True,
                text=True
            )

            print(f"✅ Cost comment posted to PR #{pr_number}")
            print(f"   Main task: ${main_cost_val:.6f}")
            print(f"   PR summary: ${summary_cost_val:.6f}")
            print(f"   Total: ${total_cost:.6f}")

            gh.write_output("comment_posted", "true")
            return 0

        finally:
            # Clean up temp file
            os.unlink(temp_file)

    except subprocess.CalledProcessError as e:
        gh.set_error(f"Failed to post comment: {e.stderr}")
        return 1
    except Exception as e:
        gh.set_error(f"Error posting cost comment: {str(e)}")
        return 1


def format_cost_comment(main_cost: float, summary_cost: float, total_cost: float, repo: str, run_id: str) -> str:
    """
    Format the cost breakdown comment with nice formatting.

    Args:
        main_cost: Cost of main task in USD
        summary_cost: Cost of PR summary in USD
        total_cost: Total cost in USD
        repo: Repository name (owner/repo)
        run_id: Workflow run ID

    Returns:
        Formatted markdown comment
    """
    workflow_url = f"https://github.com/{repo}/actions/runs/{run_id}"

    comment = f"""## 💰 Cost Breakdown

This PR was generated using Claude Code with the following costs:

| Component | Cost (USD) |
|-----------|------------|
| Main refactoring task | ${main_cost:.6f} |
| PR summary generation | ${summary_cost:.6f} |
| **Total** | **${total_cost:.6f}** |

---
*Cost tracking by ClaudeStep • [View workflow run]({workflow_url})*
"""

    return comment
