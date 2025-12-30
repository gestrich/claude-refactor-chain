"""Service Layer class for reviewer management operations.

Follows Service Layer pattern (Fowler, PoEAA) - encapsulates business logic
for reviewer capacity checking and assignment.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from claudestep.services.artifact_operations_service import find_project_artifacts
from claudestep.services.metadata_service import MetadataService
from claudestep.domain.models import ReviewerCapacityResult
from claudestep.domain.project_configuration import ProjectConfiguration


class ReviewerManagementService:
    """Service Layer class for reviewer management operations.

    Coordinates reviewer capacity checking and assignment by orchestrating
    artifact operations and metadata queries. Implements business logic for
    ClaudeStep's reviewer assignment workflow.
    """

    def __init__(self, repo: str, metadata_service: MetadataService):
        self.repo = repo
        self.metadata_service = metadata_service

    # Public API methods

    def find_available_reviewer(
        self, config: ProjectConfiguration, label: str, project: str
    ) -> tuple[Optional[str], ReviewerCapacityResult]:
        """Find first reviewer with capacity based on artifact metadata

        Args:
            config: ProjectConfiguration domain model with reviewers
            label: GitHub label to filter PRs
            project: Project name to match

        Returns:
            Tuple of (username or None, ReviewerCapacityResult)
        """
        result = ReviewerCapacityResult()

        # Initialize reviewer PR lists
        reviewer_prs = defaultdict(list)
        for reviewer in config.reviewers:
            reviewer_prs[reviewer.username] = []

        # Find open PR artifacts for this project
        artifacts = find_project_artifacts(
            repo=self.repo,
            project=project,
            label=label,
            pr_state="open",
            download_metadata=True
        )

        # Group open PRs by reviewer from artifact metadata
        for artifact in artifacts:
            if artifact.metadata:
                assigned_reviewer = artifact.metadata.reviewer

                # Check if this reviewer is in our list
                if assigned_reviewer in reviewer_prs:
                    task_description = artifact.metadata.task_description or f"Task {artifact.metadata.task_index}"

                    pr_info = {
                        "pr_number": artifact.metadata.pr_number,
                        "task_index": artifact.metadata.task_index,
                        "task_description": task_description
                    }
                    reviewer_prs[assigned_reviewer].append(pr_info)
                    print(f"PR #{artifact.metadata.pr_number}: reviewer={assigned_reviewer}")
                else:
                    print(f"Warning: PR #{artifact.metadata.pr_number} has unknown reviewer: {assigned_reviewer}")

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
