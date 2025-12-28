"""Shared fixtures for E2E integration tests.

This module provides pytest fixtures used across E2E tests, including
GitHub helper instances, test project management, and cleanup utilities.
"""

import uuid
import pytest
from pathlib import Path
from typing import Generator, List

from .helpers.github_helper import GitHubHelper
from .helpers.project_manager import TestProjectManager


@pytest.fixture
def gh() -> GitHubHelper:
    """Provide a GitHubHelper instance for tests.

    Returns:
        Configured GitHubHelper instance for claude-step repository
    """
    return GitHubHelper(repo="gestrich/claude-step")


@pytest.fixture
def project_id() -> str:
    """Generate a unique project ID for test isolation.

    Returns:
        Unique 8-character hex string
    """
    return uuid.uuid4().hex[:8]


@pytest.fixture
def project_manager() -> TestProjectManager:
    """Provide a TestProjectManager instance.

    Returns:
        Configured TestProjectManager instance
    """
    return TestProjectManager()


@pytest.fixture
def test_project(
    project_manager: TestProjectManager,
    project_id: str
) -> Generator[str, None, None]:
    """Create and cleanup a test project.

    This fixture:
    1. Creates a test project before the test
    2. Yields the project name to the test
    3. Cleans up the project after the test (even on failure)

    Args:
        project_manager: TestProjectManager fixture
        project_id: Unique project ID fixture

    Yields:
        Project name (e.g., "test-project-abc123")
    """
    project_name = project_manager.create_test_project(project_id=project_id)

    try:
        yield project_name
    finally:
        # Cleanup: delete project from filesystem
        try:
            project_manager.delete_test_project(project_name)
        except Exception as e:
            print(f"Warning: Failed to cleanup test project {project_name}: {e}")


@pytest.fixture
def cleanup_prs(gh: GitHubHelper) -> Generator[List[int], None, None]:
    """Track and cleanup PRs created during tests.

    Usage in tests:
        def test_something(cleanup_prs):
            # Create PR
            pr_number = create_pr()
            cleanup_prs.append(pr_number)
            # Test continues...

    Yields:
        List to append PR numbers to for cleanup
    """
    pr_numbers: List[int] = []

    try:
        yield pr_numbers
    finally:
        # Cleanup: close all tracked PRs
        for pr_number in pr_numbers:
            try:
                gh.close_pull_request(pr_number)
            except Exception as e:
                print(f"Warning: Failed to close PR #{pr_number}: {e}")
