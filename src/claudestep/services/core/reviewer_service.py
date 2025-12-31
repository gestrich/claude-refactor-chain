"""Core service for reviewer management operations.

Follows Service Layer pattern (Fowler, PoEAA) - encapsulates business logic
for reviewer capacity checking and assignment.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from claudestep.services.core.pr_service import PRService
from claudestep.domain.models import ReviewerCapacityResult
from claudestep.domain.project_configuration import ProjectConfiguration


class ReviewerService:
    """Core service for reviewer management operations.

    Coordinates reviewer capacity checking and assignment by querying
    GitHub API for open PRs. Implements business logic for ClaudeStep's
    reviewer assignment workflow.
    """

    def __init__(self, repo: str, pr_service: PRService):
        self.repo = repo
        self.pr_service = pr_service

    # Public API methods

    def find_available_reviewer(
        self, config: ProjectConfiguration, label: str, project: str
    ) -> tuple[Optional[str], ReviewerCapacityResult]:
        """Find first reviewer with capacity based on GitHub API queries

        Args:
            config: ProjectConfiguration domain model with reviewers
            label: GitHub label to filter PRs
            project: Project name to match (used for filtering by branch name pattern)

        Returns:
            Tuple of (username or None, ReviewerCapacityResult)
        """
        result = ReviewerCapacityResult()

        # Initialize reviewer PR lists
        reviewer_prs = defaultdict(list)
        for reviewer in config.reviewers:
            reviewer_prs[reviewer.username] = []

        # Query open PRs for each reviewer from GitHub API using PRService
        for reviewer in config.reviewers:
            username = reviewer.username

            # Get open PRs for this reviewer on this project using service layer
            prs = self.pr_service.get_reviewer_prs_for_project(
                username=username,
                project=project,
                label=label
            )

            # Build PR info list using domain model properties
            for pr in prs:
                pr_info = {
                    "pr_number": pr.number,
                    "task_index": pr.task_index,
                    "task_description": pr.task_description
                }
                reviewer_prs[username].append(pr_info)
                print(f"PR #{pr.number}: reviewer={username}")

        # Build result and find first available reviewer
        selected_reviewer = None
        for reviewer in config.reviewers:
            username = reviewer.username
            max_prs = reviewer.max_open_prs
            open_prs = reviewer_prs[username]
            has_capacity = len(open_prs) < max_prs

            # Add to result
            result.add_reviewer(username, max_prs, open_prs, has_capacity)

            print(f"Reviewer {username}: {len(open_prs)} open PRs (max: {max_prs})")

            # Select first available reviewer
            if has_capacity and selected_reviewer is None:
                selected_reviewer = username
                print(f"Selected reviewer: {username}")

        result.selected_reviewer = selected_reviewer
        result.all_at_capacity = (selected_reviewer is None)

        return selected_reviewer, result
