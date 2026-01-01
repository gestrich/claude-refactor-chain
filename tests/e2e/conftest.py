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
from .helpers.test_branch_manager import TestBranchManager
from .constants import E2E_TEST_BRANCH


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
def test_project() -> str:
    """Provide the permanent E2E test project name.

    This fixture returns the name of the permanent test project that exists
    in the main branch at claude-step/e2e-test-project/.

    With the new spec-file-source-of-truth design, test projects must exist
    in the main branch. Instead of creating temporary projects, E2E tests now
    use a permanent test project with 300+ tasks.

    Returns:
        Project name: "e2e-test-project"
    """
    return "e2e-test-project"




@pytest.fixture(scope="session", autouse=True)
def test_branch():
    """Ensure test branch exists before running tests.

    This fixture validates that the main-e2e branch has been set up
    by the E2E test workflow before tests run. The branch should already
    be created and configured by the workflow.

    The branch name is defined by the E2E_TEST_BRANCH constant to ensure
    consistency across all E2E test helpers and fixtures.

    Yields:
        None - Just ensures branch validation happens
    """
    # Branch should already be set up by workflow
    # This fixture provides a place to add validation if needed in the future
    manager = TestBranchManager()
    # Could add validation here to ensure branch exists
    yield
    # Cleanup handled by workflow


@pytest.fixture(scope="session", autouse=True)
def cleanup_previous_test_runs():
    """Clean up resources from previous test runs at test start.

    This fixture runs once before all tests to ensure a clean state.
    Cleanup at test START (not end) allows manual inspection of test results.

    Cleanup tasks:
    - Delete old main-e2e branch if it exists
    - Close any open PRs with "claudestep" label
    - Remove "claudestep" label from ALL PRs (open and closed)
    - Clean up test branches from previous failed runs

    Yields:
        None - Just ensures cleanup happens before tests
    """
    gh = GitHubHelper(repo="gestrich/claude-step")

    # Delete old main-e2e branch if it exists
    try:
        gh.delete_branch("main-e2e")
    except Exception as e:
        # Branch might not exist, which is fine
        pass

    # Clean up test branches from previous failed runs
    gh.cleanup_test_branches(pattern_prefix="claude-step-test-")

    # Get all PRs with claudestep label (both open and closed)
    from claudestep.domain.constants import DEFAULT_PR_LABEL
    from claudestep.infrastructure.github.operations import list_pull_requests

    # Close open PRs with claudestep label
    try:
        open_prs = list_pull_requests(
            repo=gh.repo,
            state="open",
            label=DEFAULT_PR_LABEL,
            limit=100
        )
        for pr in open_prs:
            try:
                gh.close_pull_request(pr.number)
            except Exception as e:
                print(f"Warning: Failed to close PR #{pr.number}: {e}")
    except Exception as e:
        print(f"Warning: Failed to list open PRs: {e}")

    # Remove claudestep label from ALL PRs (open and closed)
    try:
        all_prs = list_pull_requests(
            repo=gh.repo,
            state="all",
            label=DEFAULT_PR_LABEL,
            limit=100
        )
        for pr in all_prs:
            try:
                gh.remove_label_from_pr(pr.number, DEFAULT_PR_LABEL)
            except Exception as e:
                # Label might not exist on the PR, which is fine
                pass
    except Exception as e:
        print(f"Warning: Failed to remove labels from PRs: {e}")

    yield
    # No post-test cleanup - artifacts remain for manual inspection
