"""End-to-End tests for ClaudeStep workflow.

This module contains E2E integration tests that verify the ClaudeStep workflow
creates PRs correctly, generates AI summaries, includes cost information, and
tests the real user workflows (push-triggered and merge-triggered).

The tests use a recursive workflow pattern where the claude-step repository
tests itself by running the actual claudestep.yml workflow against the main-e2e
branch with dynamically generated test projects.

TESTS IN THIS MODULE:

1. test_auto_start_workflow
   - What: Verifies pushing spec to main-e2e triggers claudestep.yml and PR creation
   - Why E2E: Tests real user flow of push-triggered automatic PR generation

2. test_merge_triggered_workflow
   - What: Verifies merging a PR triggers creation of the next PR
   - Why E2E: Tests GitHub Actions trigger-on-merge integration
"""

from .helpers.github_helper import GitHubHelper


def test_auto_start_workflow(
    gh: GitHubHelper,
    setup_test_project: str
) -> None:
    """Test that claudestep.yml triggers when spec is pushed to main-e2e.

    This test validates the real user flow where pushing a spec to main-e2e
    automatically triggers PR creation via the push-triggered workflow.

    The test verifies:
    1. Pushing spec to main-e2e triggers claudestep.yml workflow (push event)
    2. Workflow completes successfully
    3. Workflow creates a PR for the first task
    4. PR has "claudestep" label
    5. PR targets main-e2e branch
    6. PR has AI summary comment with cost breakdown

    Cleanup happens at test START (not end) to allow manual inspection.

    Args:
        gh: GitHub helper fixture
        setup_test_project: Test project created and pushed to main-e2e
    """
    from claudestep.domain.constants import DEFAULT_PR_LABEL
    from tests.e2e.constants import E2E_TEST_BRANCH

    test_project = setup_test_project

    # Wait for claudestep workflow to start (triggered by push)
    gh.wait_for_workflow_to_start(
        workflow_name="claudestep.yml",
        timeout=60,
        branch=E2E_TEST_BRANCH
    )

    # Wait for workflow to complete
    workflow_run = gh.wait_for_workflow_completion(
        workflow_name="claudestep.yml",
        timeout=900,  # 15 minutes
        branch=E2E_TEST_BRANCH
    )

    assert workflow_run.conclusion == "success", \
        f"Workflow should complete successfully. Run URL: {workflow_run.url}"

    # Get all PRs for this project
    project_prs = gh.get_pull_requests_for_project(test_project)

    assert len(project_prs) > 0, \
        f"At least one PR should be created for project '{test_project}'. Workflow run: {workflow_run.url}"

    # Get the first (most recent) PR
    pr = project_prs[0]
    pr_url = f"https://github.com/gestrich/claude-step/pull/{pr.number}"

    # Verify PR is open
    assert pr.state == "open", \
        f"PR #{pr.number} should be open but is {pr.state}. PR URL: {pr_url}"

    # Verify PR has claudestep label
    assert DEFAULT_PR_LABEL in [label.lower() for label in pr.labels], \
        f"PR #{pr.number} should have '{DEFAULT_PR_LABEL}' label. PR URL: {pr_url}"

    # Verify PR targets main-e2e branch
    assert pr.base_ref_name == E2E_TEST_BRANCH, \
        f"PR #{pr.number} should target '{E2E_TEST_BRANCH}' branch but targets '{pr.base_ref_name}'. PR URL: {pr_url}"

    # Verify PR has a title
    assert pr.title, f"PR #{pr.number} should have a title. PR URL: {pr_url}"

    # Get PR comments for summary and cost verification
    comments = gh.get_pr_comments(pr.number)

    # Verify there's at least one comment
    assert len(comments) > 0, \
        f"PR #{pr.number} should have at least one comment. PR URL: {pr_url}"

    # Extract comment bodies for analysis
    comment_bodies = [c.body for c in comments]

    # Verify PR has a combined comment with both summary and cost breakdown
    has_combined_comment = any(
        "## AI-Generated Summary" in body and "## 💰 Cost Breakdown" in body
        for body in comment_bodies
    )
    assert has_combined_comment, \
        f"PR #{pr.number} should have a combined comment with both '## AI-Generated Summary' and '## 💰 Cost Breakdown' headers. " \
        f"Found {len(comments)} comment(s). PR URL: {pr_url}"


def test_merge_triggered_workflow(
    gh: GitHubHelper,
    setup_test_project: str
) -> None:
    """Test that merging a PR triggers creation of the next PR.

    This test verifies that when a ClaudeStep PR is merged, the workflow
    automatically triggers and creates a PR for the next task in the spec.

    The test verifies:
    1. Push triggers claudestep.yml and creates first PR
    2. Merging the first PR triggers claudestep.yml workflow via push event
    3. Workflow creates a second PR for the next task
    4. Second PR has "claudestep" label
    5. Second PR targets main-e2e branch

    Cleanup happens at test START (not end) to allow manual inspection.

    Args:
        gh: GitHub helper fixture
        setup_test_project: Test project created and pushed to main-e2e (has 3 tasks)
    """
    from claudestep.domain.constants import DEFAULT_PR_LABEL
    from tests.e2e.constants import E2E_TEST_BRANCH

    test_project = setup_test_project

    # Wait for claudestep workflow to start (triggered by push from setup)
    gh.wait_for_workflow_to_start(
        workflow_name="claudestep.yml",
        timeout=60,
        branch=E2E_TEST_BRANCH
    )

    # Wait for workflow to complete (creates first PR)
    first_workflow_run = gh.wait_for_workflow_completion(
        workflow_name="claudestep.yml",
        timeout=900,  # 15 minutes
        branch=E2E_TEST_BRANCH
    )

    assert first_workflow_run.conclusion == "success", \
        f"First workflow run should complete successfully. Run URL: {first_workflow_run.url}"

    # Get the first PR that was created
    project_prs = gh.get_pull_requests_for_project(test_project)
    assert len(project_prs) > 0, \
        f"At least one PR should be created for project '{test_project}'. Workflow run: {first_workflow_run.url}"

    first_pr = project_prs[0]
    first_pr_url = f"https://github.com/gestrich/claude-step/pull/{first_pr.number}"

    # Verify first PR is open
    assert first_pr.state == "open", \
        f"First PR #{first_pr.number} should be open. PR URL: {first_pr_url}"

    # Merge the first PR (this should trigger the workflow via PR close event)
    gh.merge_pull_request(first_pr.number)

    # Wait for the workflow to be triggered by the PR merge
    gh.wait_for_workflow_to_start(
        workflow_name="claudestep.yml",
        timeout=60,
        branch=E2E_TEST_BRANCH
    )

    # Wait for the second workflow run to complete (creates second PR)
    second_workflow_run = gh.wait_for_workflow_completion(
        workflow_name="claudestep.yml",
        timeout=900,  # 15 minutes
        branch=E2E_TEST_BRANCH
    )

    assert second_workflow_run.conclusion == "success", \
        f"Second workflow run should complete successfully. Run URL: {second_workflow_run.url}"

    # Get all PRs for this project again
    project_prs = gh.get_pull_requests_for_project(test_project)

    # We should now have 2 PRs: first one (merged) and second one (open)
    assert len(project_prs) >= 2, \
        f"At least 2 PRs should exist for project '{test_project}' after merge. " \
        f"Found {len(project_prs)} PR(s). Second workflow run: {second_workflow_run.url}"

    # Find the second PR (should be open, not the merged one)
    open_prs = [pr for pr in project_prs if pr.state == "open"]
    assert len(open_prs) > 0, \
        f"At least one open PR should exist after merging first PR. " \
        f"Found {len(open_prs)} open PR(s). Second workflow run: {second_workflow_run.url}"

    second_pr = open_prs[0]
    second_pr_url = f"https://github.com/gestrich/claude-step/pull/{second_pr.number}"

    # Verify second PR has claudestep label
    assert DEFAULT_PR_LABEL in [label.lower() for label in second_pr.labels], \
        f"Second PR #{second_pr.number} should have '{DEFAULT_PR_LABEL}' label. PR URL: {second_pr_url}"

    # Verify second PR targets main-e2e branch
    assert second_pr.base_ref_name == E2E_TEST_BRANCH, \
        f"Second PR #{second_pr.number} should target '{E2E_TEST_BRANCH}' branch but targets '{second_pr.base_ref_name}'. " \
        f"PR URL: {second_pr_url}"

    # Verify second PR is different from first PR
    assert second_pr.number != first_pr.number, \
        f"Second PR should be different from first PR. Both have number {first_pr.number}"