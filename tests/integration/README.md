# ClaudeStep Integration Tests

End-to-end integration tests for the ClaudeStep GitHub Actions workflow.

## Overview

The integration test validates the complete ClaudeStep workflow by:

1. Creating a test project in the demo repository
2. Triggering the workflow and verifying PR creation
3. Testing reviewer capacity limits (max 2 open PRs)
4. Testing the merge trigger functionality
5. Cleaning up all created resources

## Prerequisites

### 1. GitHub CLI

Install and authenticate the GitHub CLI:

```bash
# Install gh CLI (macOS)
brew install gh

# Or on Linux
# See https://github.com/cli/cli/blob/trunk/docs/install_linux.md

# Authenticate
gh auth login
```

### 2. Python Dependencies

```bash
pip install pytest
```

### 3. Repository Access

You need write access to the `gestrich/claude-step-demo` repository (or update the test to use your own fork).

### 4. Git Configuration

The test will use your local git configuration for commits. Ensure git is configured:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Running the Test

### Run with pytest

```bash
# From repository root
pytest tests/integration/test_workflow_e2e.py -v -s

# Or run directly
python tests/integration/test_workflow_e2e.py
```

### Test Output

The test provides detailed output showing:
- Project creation and setup
- Workflow run IDs and status
- PR creation and verification
- Cleanup operations

Example output:
```
============================================================
Testing ClaudeStep workflow with project: test-project-a1b2c3d4
============================================================

[STEP 1] Triggering workflow for first task...
  Workflow run ID: 123456789
  Status: in_progress, Conclusion: None
  Status: completed, Conclusion: success
  ✓ Workflow completed successfully
  ✓ PR #42 created: ClaudeStep: Create test-file-1.txt

[STEP 2] Triggering workflow for second task...
  Workflow run ID: 123456790
  ✓ Workflow completed successfully
  ✓ PR #43 created: ClaudeStep: Create test-file-2.txt
  ✓ Reviewer at capacity with 2 open PRs

[STEP 3] Merging first PR to test merge trigger...
  ✓ Merged PR #42
  Waiting for merge trigger to start workflow...
  Workflow run ID: 123456791
  ✓ Merge-triggered workflow completed successfully
  ✓ PR #44 created: ClaudeStep: Create test-file-3.txt

============================================================
✓ All tests passed!
============================================================
```

## What the Test Validates

### 1. Manual Workflow Trigger
- Workflow can be triggered via `workflow_dispatch`
- Correct project is processed
- PR is created for the first uncompleted task

### 2. Reviewer Capacity Management
- When reviewer has 2 open PRs (at capacity), workflow processes next task
- New PR is created for different task (not same as open PR)
- Both PRs remain open

### 3. Merge Trigger
- When a PR with the project label is merged, workflow is triggered
- New PR is created for the next uncompleted task
- Workflow correctly processes tasks in order

### 4. Resource Cleanup
- Test project is removed from repository
- Test PRs are closed
- Repository is left in clean state

## Cleanup

The test automatically cleans up:
- Test project files (removed from main branch)
- Test PRs (closed and branches deleted)

If a test fails or is interrupted, you may need to manually clean up:

```bash
# Close any test PRs
gh pr list --repo gestrich/claude-step-demo --label "claudestep-test-project-*"
gh pr close <PR_NUMBER> --delete-branch

# Remove test project from repository
cd /path/to/claude-step-demo
git rm -rf refactor/test-project-*
git commit -m "Remove test project"
git push origin main
```

## Troubleshooting

### Test times out waiting for workflow

- Check GitHub Actions quotas/limits
- Verify the workflow file exists in the demo repository
- Check workflow run logs in GitHub Actions UI

### PRs not created

- Verify ANTHROPIC_API_KEY is configured in repository secrets
- Check workflow run logs for errors
- Verify spec.md format is correct

### Authentication errors

- Run `gh auth status` to verify authentication
- Run `gh auth refresh` if token expired
- Ensure you have write access to the repository

### Cleanup fails

- Manually close PRs via GitHub UI or `gh pr close`
- Manually remove test project directory and push to main

## CI/CD Integration

To run this test in CI:

1. Add `gh` CLI to CI environment
2. Authenticate with `gh auth login --with-token < $GH_TOKEN`
3. Set up git configuration
4. Run pytest

Example GitHub Actions workflow:

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install pytest

      - name: Authenticate gh CLI
        run: echo "${{ secrets.GITHUB_TOKEN }}" | gh auth login --with-token

      - name: Configure git
        run: |
          git config --global user.name "GitHub Actions"
          git config --global user.email "actions@github.com"

      - name: Run integration tests
        run: pytest tests/integration/test_workflow_e2e.py -v -s
```

## Notes

- Test creates real PRs and workflow runs in the demo repository
- Each test run takes 5-10 minutes (workflows take time to execute)
- Test is safe to run multiple times (creates unique project IDs)
- Random project ID prevents conflicts between parallel test runs
