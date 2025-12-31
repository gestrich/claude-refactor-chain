"""Core service for task management operations.

Follows Service Layer pattern (Fowler, PoEAA) - encapsulates business logic
for task finding, marking, and tracking operations.
"""

import os
import re
from typing import Optional

from claudestep.domain.exceptions import FileNotFoundError
from claudestep.domain.spec_content import SpecContent, generate_task_hash
from claudestep.services.core.pr_service import PRService


class TaskService:
    """Core service for task management operations.

    Coordinates task finding, marking, and tracking by orchestrating
    domain models and infrastructure operations. Implements business
    logic for ClaudeStep's task workflow.
    """

    def __init__(self, repo: str, pr_service: PRService):
        """Initialize TaskService

        Args:
            repo: GitHub repository (owner/name)
            pr_service: Service for PR operations
        """
        self.repo = repo
        self.pr_service = pr_service

    # Public API methods

    def find_next_available_task(self, spec: SpecContent, skip_indices: Optional[set] = None, skip_hashes: Optional[set] = None) -> Optional[tuple]:
        """Find first unchecked task not in skip_indices or skip_hashes

        Args:
            spec: SpecContent domain model
            skip_indices: Set of task indices to skip (legacy support for old index-based PRs)
            skip_hashes: Set of task hashes to skip (in-progress tasks with hash-based PRs)

        Returns:
            Tuple of (task_index, task_text, task_hash) or None if no available task found
            task_index is 1-based position in spec.md
            task_hash is 8-character hash of task description
        """
        if skip_indices is None:
            skip_indices = set()
        if skip_hashes is None:
            skip_hashes = set()

        task = spec.get_next_available_task(skip_indices, skip_hashes)
        if task:
            # Print skip messages for any tasks we're skipping
            for skipped_task in spec.tasks:
                if not skipped_task.is_completed and skipped_task.index < task.index:
                    # Check if task is being skipped by index (legacy)
                    if skipped_task.index in skip_indices:
                        print(f"Skipping task {skipped_task.index} (already in progress - index-based PR)")
                    # Check if task is being skipped by hash (new)
                    elif skipped_task.task_hash in skip_hashes:
                        print(f"Skipping task {skipped_task.index} (already in progress - hash {skipped_task.task_hash[:6]}...)")

            return (task.index, task.description, task.task_hash)

        return None

    @staticmethod
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

    def get_in_progress_tasks(self, label: str, project: str) -> tuple[set, set]:
        """Get task identifiers currently being worked on (indices and hashes)

        Args:
            label: GitHub label to filter PRs
            project: Project name to match

        Returns:
            Tuple of (task_indices, task_hashes) where:
            - task_indices: Set of task indices from old index-based PRs
            - task_hashes: Set of task hashes from new hash-based PRs
        """
        try:
            # Query open PRs for this project using service abstraction
            open_prs = self.pr_service.get_open_prs_for_project(project, label=label)

            # Extract task identifiers using domain model properties
            task_indices = set()
            task_hashes = set()

            for pr in open_prs:
                # Check for hash-based PR (new format)
                if pr.task_hash is not None:
                    task_hashes.add(pr.task_hash)
                # Check for index-based PR (legacy format)
                elif pr.task_index is not None:
                    task_indices.add(pr.task_index)

            return (task_indices, task_hashes)
        except Exception as e:
            print(f"Error: Failed to query GitHub PRs: {e}")
            return (set(), set())

    def get_in_progress_task_indices(self, label: str, project: str) -> set:
        """Get set of task indices currently being worked on (legacy compatibility)

        DEPRECATED: Use get_in_progress_tasks() instead for full hash support.
        This method only returns indices for backward compatibility.

        Args:
            label: GitHub label to filter PRs
            project: Project name to match

        Returns:
            Set of task indices that are in progress (from old index-based PRs)
        """
        task_indices, _ = self.get_in_progress_tasks(label, project)
        return task_indices

    def detect_orphaned_prs(self, label: str, project: str, spec: 'SpecContent') -> list:
        """Detect PRs that reference tasks no longer in spec (orphaned PRs)

        An orphaned PR is one where:
        - The task hash doesn't match any current task hash in spec.md (for hash-based PRs)
        - The task index is out of range or points to a different task (for index-based PRs)

        Args:
            label: GitHub label to filter PRs
            project: Project name to match
            spec: SpecContent domain model with current tasks

        Returns:
            List of orphaned GitHubPullRequest objects
        """
        try:
            # Query all open PRs for this project
            open_prs = self.pr_service.get_open_prs_for_project(project, label=label)

            # Build sets of valid task identifiers from current spec
            valid_hashes = {task.task_hash for task in spec.tasks}
            valid_indices = {task.index for task in spec.tasks}

            orphaned_prs = []

            for pr in open_prs:
                # Check hash-based PRs
                if pr.task_hash is not None:
                    if pr.task_hash not in valid_hashes:
                        orphaned_prs.append(pr)
                # Check index-based PRs
                elif pr.task_index is not None:
                    if pr.task_index not in valid_indices:
                        orphaned_prs.append(pr)

            return orphaned_prs
        except Exception as e:
            print(f"Warning: Failed to detect orphaned PRs: {e}")
            return []

    # Static utility methods

    @staticmethod
    def generate_task_hash(description: str) -> str:
        """Generate stable hash identifier for a task description.

        Uses SHA-256 hash truncated to 8 characters for readability.
        This provides a stable identifier that doesn't change when tasks
        are reordered in spec.md, only when the description itself changes.

        Args:
            description: Task description text

        Returns:
            8-character hash string (lowercase hexadecimal)

        Examples:
            >>> TaskService.generate_task_hash("Add user authentication")
            'a3f2b891'
            >>> TaskService.generate_task_hash("  Add user authentication  ")
            'a3f2b891'  # Same hash after whitespace normalization
            >>> TaskService.generate_task_hash("")
            'e3b0c442'  # Hash of empty string
        """
        # Delegate to domain model function
        return generate_task_hash(description)

    @staticmethod
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
