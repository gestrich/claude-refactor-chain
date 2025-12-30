"""GitHub domain models for ClaudeStep

These models represent GitHub API objects with type-safe properties and methods.
They encapsulate JSON parsing to ensure the service layer works with well-formed
domain objects rather than raw dictionaries.

Following the principle: "Parse once into well-formed models"
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class GitHubUser:
    """Domain model for GitHub user

    Represents a GitHub user from API responses with type-safe properties.
    """

    login: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'GitHubUser':
        """Parse from GitHub API response

        Args:
            data: Dictionary from GitHub API (e.g., assignee object)

        Returns:
            GitHubUser instance with parsed data

        Example:
            >>> user_data = {"login": "octocat", "name": "The Octocat"}
            >>> user = GitHubUser.from_dict(user_data)
        """
        return cls(
            login=data["login"],
            name=data.get("name"),
            avatar_url=data.get("avatar_url")
        )


@dataclass
class GitHubPullRequest:
    """Domain model for GitHub pull request

    Represents a PR from GitHub API with type-safe properties and helper methods.
    All date parsing and JSON navigation happens in from_dict() constructor.
    """

    number: int
    title: str
    state: str  # "open", "closed", "merged"
    created_at: datetime
    merged_at: Optional[datetime]
    assignees: List[GitHubUser]
    labels: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> 'GitHubPullRequest':
        """Parse from GitHub API response

        Handles all JSON parsing, date conversion, and nested object construction.
        Service layer receives clean, type-safe objects.

        Args:
            data: Dictionary from GitHub API (gh pr list --json output)

        Returns:
            GitHubPullRequest instance with all fields parsed

        Example:
            >>> pr_data = {
            ...     "number": 123,
            ...     "title": "Add feature",
            ...     "state": "OPEN",
            ...     "createdAt": "2024-01-01T12:00:00Z",
            ...     "mergedAt": None,
            ...     "assignees": [{"login": "reviewer"}],
            ...     "labels": [{"name": "claudestep"}]
            ... }
            >>> pr = GitHubPullRequest.from_dict(pr_data)
        """
        # Parse created_at (always present)
        created_at = data["createdAt"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        # Parse merged_at (optional)
        merged_at = data.get("mergedAt")
        if merged_at and isinstance(merged_at, str):
            merged_at = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))

        # Parse assignees (list of user objects)
        assignees = []
        for assignee_data in data.get("assignees", []):
            assignees.append(GitHubUser.from_dict(assignee_data))

        # Parse labels (list of label objects with "name" field)
        labels = []
        for label_data in data.get("labels", []):
            if isinstance(label_data, dict):
                labels.append(label_data["name"])
            else:
                # Handle case where labels are just strings
                labels.append(str(label_data))

        # Normalize state to lowercase for consistency
        state = data["state"].lower()

        return cls(
            number=data["number"],
            title=data["title"],
            state=state,
            created_at=created_at,
            merged_at=merged_at,
            assignees=assignees,
            labels=labels
        )

    def is_merged(self) -> bool:
        """Check if PR was merged

        Returns:
            True if PR is in merged state or has merged_at timestamp
        """
        return self.state == "merged" or self.merged_at is not None

    def is_open(self) -> bool:
        """Check if PR is open

        Returns:
            True if PR is in open state
        """
        return self.state == "open"

    def is_closed(self) -> bool:
        """Check if PR is closed (but not merged)

        Returns:
            True if PR is closed but not merged
        """
        return self.state == "closed" and not self.is_merged()

    def has_label(self, label: str) -> bool:
        """Check if PR has a specific label

        Args:
            label: Label name to check

        Returns:
            True if PR has the label
        """
        return label in self.labels

    def get_assignee_logins(self) -> List[str]:
        """Get list of assignee usernames

        Returns:
            List of login names for all assignees
        """
        return [assignee.login for assignee in self.assignees]


@dataclass
class GitHubPullRequestList:
    """Collection of GitHub pull requests with filtering/grouping methods

    Provides type-safe operations on PR lists without requiring service
    layer to work with raw JSON arrays.
    """

    pull_requests: List[GitHubPullRequest] = field(default_factory=list)

    @classmethod
    def from_json_array(cls, data: List[dict]) -> 'GitHubPullRequestList':
        """Parse from GitHub API JSON array

        Args:
            data: List of PR dictionaries from GitHub API

        Returns:
            GitHubPullRequestList with all PRs parsed

        Example:
            >>> prs_data = [
            ...     {"number": 1, "title": "PR 1", "state": "OPEN", ...},
            ...     {"number": 2, "title": "PR 2", "state": "MERGED", ...}
            ... ]
            >>> pr_list = GitHubPullRequestList.from_json_array(prs_data)
        """
        prs = [GitHubPullRequest.from_dict(pr_data) for pr_data in data]
        return cls(pull_requests=prs)

    def filter_by_state(self, state: str) -> 'GitHubPullRequestList':
        """Filter PRs by state

        Args:
            state: State to filter by ("open", "closed", "merged")

        Returns:
            New GitHubPullRequestList with filtered PRs
        """
        filtered = [pr for pr in self.pull_requests if pr.state == state.lower()]
        return GitHubPullRequestList(pull_requests=filtered)

    def filter_by_label(self, label: str) -> 'GitHubPullRequestList':
        """Filter PRs by label

        Args:
            label: Label name to filter by

        Returns:
            New GitHubPullRequestList with PRs that have the label
        """
        filtered = [pr for pr in self.pull_requests if pr.has_label(label)]
        return GitHubPullRequestList(pull_requests=filtered)

    def filter_merged(self) -> 'GitHubPullRequestList':
        """Get only merged PRs

        Returns:
            New GitHubPullRequestList with only merged PRs
        """
        filtered = [pr for pr in self.pull_requests if pr.is_merged()]
        return GitHubPullRequestList(pull_requests=filtered)

    def filter_open(self) -> 'GitHubPullRequestList':
        """Get only open PRs

        Returns:
            New GitHubPullRequestList with only open PRs
        """
        filtered = [pr for pr in self.pull_requests if pr.is_open()]
        return GitHubPullRequestList(pull_requests=filtered)

    def filter_by_date(self, since: datetime, date_field: str = "created_at") -> 'GitHubPullRequestList':
        """Filter PRs by date

        Args:
            since: Minimum date (PRs on or after this date)
            date_field: Which date field to check ("created_at" or "merged_at")

        Returns:
            New GitHubPullRequestList with PRs matching date criteria
        """
        filtered = []
        for pr in self.pull_requests:
            if date_field == "created_at":
                if pr.created_at >= since:
                    filtered.append(pr)
            elif date_field == "merged_at":
                if pr.merged_at and pr.merged_at >= since:
                    filtered.append(pr)
        return GitHubPullRequestList(pull_requests=filtered)

    def group_by_assignee(self) -> Dict[str, List[GitHubPullRequest]]:
        """Group PRs by assignee

        PRs with multiple assignees appear in multiple groups.

        Returns:
            Dictionary mapping assignee login to list of PRs
        """
        grouped: Dict[str, List[GitHubPullRequest]] = {}
        for pr in self.pull_requests:
            for assignee in pr.assignees:
                if assignee.login not in grouped:
                    grouped[assignee.login] = []
                grouped[assignee.login].append(pr)
        return grouped

    def count(self) -> int:
        """Get count of PRs in list

        Returns:
            Number of PRs
        """
        return len(self.pull_requests)

    def __len__(self) -> int:
        """Allow len() to be called on GitHubPullRequestList"""
        return self.count()

    def __iter__(self):
        """Allow iteration over PRs"""
        return iter(self.pull_requests)
