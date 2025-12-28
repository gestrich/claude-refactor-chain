# End-to-End Testing Guide

This guide explains how to run the ClaudeStep end-to-end integration tests.

## Overview

The E2E tests are located in this repository at `tests/e2e/` and use a **recursive workflow pattern** where ClaudeStep tests itself. The tests validate the complete ClaudeStep workflow in a real GitHub environment:
- Creates test projects in the same repository (`claude-step/test-*`)
- Triggers the `claudestep-test.yml` workflow which runs the action on itself
- Verifies PRs are created correctly
- Verifies AI-generated PR summaries are posted as comments
- Verifies cost information in PR comments
- Tests reviewer capacity limits
- Tests merge trigger functionality
- Cleans up all created resources

### Recursive Workflow Pattern

The key innovation is that the `claude-step` repository tests itself:

1. **E2E Test Workflow** (`.github/workflows/e2e-test.yml`) runs the test suite
2. **Tests create** temporary projects in `claude-step/test-project-{id}/`
3. **Tests trigger** the ClaudeStep Test Workflow (`.github/workflows/claudestep-test.yml`)
4. **ClaudeStep Test Workflow** runs the action using `uses: ./` (current repository)
5. **Action creates PRs** in the same repository for the test project tasks
6. **Tests verify** the PRs were created correctly with summaries
7. **Tests clean up** all test resources (projects, PRs, branches)

## Prerequisites

The e2e tests require several tools and access to GitHub:

### 1. Python 3 and pytest

```bash
# Check Python version
python3 --version

# Install pytest (may require --break-system-packages on macOS)
python3 -m pip install pytest --break-system-packages
```

### 2. GitHub CLI (gh)

```bash
# Check if gh is installed
gh --version

# Install on macOS
brew install gh

# Authenticate with GitHub
gh auth login
```

### 3. Git Configuration

```bash
# Check git config
git config user.name
git config user.email

# Configure if needed
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 4. Repository Access

You need write access to the `claude-step` repository:
- The tests will create/delete test projects in `claude-step/test-*`
- The tests will create and close test PRs
- The tests will create and delete test branches

## Running the Tests

### Option 1: Use the Test Runner Script (Recommended)

The easiest way to run the tests:

```bash
# From the claude-step repository root
cd /path/to/claude-step
./tests/e2e/run_test.sh
```

This script will:
- Check all prerequisites automatically (gh CLI, pytest, Python 3.11+, git config)
- Optionally check for ANTHROPIC_API_KEY (with user confirmation)
- Run the E2E test suite with proper settings
- Display colored output for easy reading
- Support passing pytest arguments (e.g., `-v`, `-k test_name`, `--pdb`)

### Option 2: Run pytest Directly

If you prefer to run pytest directly:

```bash
# From the claude-step repository root
cd /path/to/claude-step
pytest tests/e2e/test_workflow_e2e.py -v -s
```

**Flags explained:**
- `-v` - Verbose output (shows test names)
- `-s` - Show print statements (important for test progress)
- `-k <pattern>` - Run only tests matching the pattern

### Running Individual Tests

```bash
# Run only the workflow test
pytest tests/e2e/test_workflow_e2e.py -v -s

# Run only the statistics test
pytest tests/e2e/test_statistics_e2e.py -v -s

# Run a specific test function
pytest tests/e2e/test_workflow_e2e.py::test_creates_pr_with_summary -v -s
```

## What the Tests Do

### test_workflow_e2e.py

This file contains comprehensive tests of the main ClaudeStep workflow:

**test_creates_pr_with_summary:**
1. Creates a test project with 3 tasks in `claude-step/test-project-<id>/`
2. Commits and pushes to the claude-step repo's main branch
3. Triggers the `claudestep-test.yml` workflow manually
4. Waits for workflow to complete (usually 60-120 seconds)
5. Verifies PR was created for the first task
6. Verifies AI-generated summary comment appears on the PR
7. Verifies cost information appears in the summary

**test_creates_pr_with_cost_info:**
- Validates that cost information is included in PR comments
- Checks for token usage and estimated cost

**test_reviewer_capacity:**
- Creates multiple test projects
- Triggers workflows to test `maxOpenPRs` limits
- Verifies reviewers don't exceed capacity

**test_merge_triggers_next_pr:**
- Creates a PR and merges it
- Verifies merge triggers the next workflow run
- Confirms the next task's PR is created automatically

**test_empty_spec:**
- Tests handling of projects with no tasks
- Verifies workflow completes successfully without creating PRs

### test_statistics_e2e.py

Tests the statistics collection workflow:

**test_statistics_workflow_runs_successfully:**
1. Triggers the `claudestep-statistics.yml` workflow
2. Waits for workflow completion
3. Verifies workflow succeeds or is skipped appropriately

**test_statistics_workflow_with_custom_days:**
- Tests statistics with default configuration
- Verifies workflow accepts the days_back parameter

**test_statistics_output_format:**
- Validates statistics workflow produces expected output
- Checks for proper completion status

## Expected Duration

- **Total test time**: 5-10 minutes (for full suite)
- **Per workflow run**: 60-120 seconds
- **PR summary posting**: Usually within 60 seconds of PR creation
- **Cleanup**: 5-10 seconds per test

## Understanding Test Output

The tests provide detailed progress output using pytest's verbose mode:

```
tests/e2e/test_workflow_e2e.py::test_creates_pr_with_summary
Creating test project: test-project-abc123
Workflow run ID: 12345678
Waiting for workflow completion...
  Status: queued
  Status: in_progress
  Status: completed (success)
Checking for PR...
  ✓ PR #42 created: refactor/test-project-abc123-1
  ✓ AI-generated summary found
  ✓ Cost information found
Cleaning up test resources...
  ✓ Closed PR #42
  ✓ Deleted branch refactor/test-project-abc123-1
  ✓ Removed test project
PASSED

tests/e2e/test_statistics_e2e.py::test_statistics_workflow_runs_successfully
Workflow run ID: 87654321
Waiting for workflow completion...
  Status: completed (success)
PASSED
```

## Common Issues and Solutions

### Issue: "pytest not found"

```bash
# Solution: Install pytest
python3 -m pip install pytest --break-system-packages
```

### Issue: "gh CLI not authenticated"

```bash
# Solution: Authenticate with GitHub
gh auth login
# Follow the prompts to authenticate
```

### Issue: "git not configured"

```bash
# Solution: Configure git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### Issue: "No AI-generated summary found"

This usually means:
1. The PR summary feature is not enabled in the workflow (check `add_pr_summary` input)
2. The ANTHROPIC_API_KEY secret is not configured
3. The workflow step failed (check workflow logs)

**Solution:** Check the workflow run logs:
```bash
# Get the workflow run ID from test output
gh run view <run_id> --repo gestrich/claude-step --log | grep -i summary
```

### Issue: Test hangs or times out

- Check your network connection
- Verify GitHub Actions is not experiencing issues
- The demo repository may have rate limits

### Issue: "Updates were rejected" during cleanup

This is usually harmless - it means another test or process modified the repo during cleanup. The test will still pass if PRs were verified correctly.

## Viewing Test Results in GitHub

After the test completes, you can view the actual PRs and workflow runs:

```bash
# View a specific PR (number from test output)
gh pr view <pr_number> --repo gestrich/claude-step

# View PR comments (including AI summary)
gh pr view <pr_number> --repo gestrich/claude-step --json comments

# View workflow run logs
gh run view <run_id> --repo gestrich/claude-step --log
```

## Test Configuration

The tests use fixtures defined in `tests/e2e/conftest.py`:

- **Repository**: `gestrich/claude-step` (configured in `GitHubHelper`)
- **Workflow**: `claudestep-test.yml` (recursive workflow)
- **Reviewer capacity**: 2 PRs (configured in test projects)
- **Workflow timeout**: 300 seconds (5 minutes)
- **Test project naming**: `test-project-{uuid}` for isolation

## CI/CD Integration

E2E tests can be run in GitHub Actions using the `.github/workflows/e2e-test.yml` workflow:

```yaml
name: E2E Integration Tests

on:
  workflow_dispatch:  # Manual trigger
  pull_request:
    types: [closed]   # Optional: Run after merges

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install pytest pyyaml

      - name: Run E2E tests
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: ./tests/e2e/run_test.sh
```

**Note:** E2E tests are typically run manually due to API costs and execution time. They can be triggered via:
- Manual workflow dispatch from GitHub UI
- On-demand via `gh workflow run e2e-test.yml`
- Optionally on PR merges to main

## Important Notes

1. **Real GitHub Operations**: These tests create real PRs and trigger real workflows in the claude-step repository
2. **API Costs**: Each test run uses Claude API credits for workflow execution and PR summary generation
3. **Cleanup**: Tests clean up after themselves automatically using pytest fixtures
4. **Test Isolation**: Each test uses unique project IDs (`test-project-{uuid}`) to prevent conflicts
5. **Self-Testing**: The action tests itself using the recursive workflow pattern (`uses: ./`)
6. **Test Artifacts**: All test projects, PRs, and branches are temporary and cleaned up automatically

## Troubleshooting Failed Tests

If a test fails:

1. **Check the test output** - It shows which step failed and why
2. **View the workflow logs** - Use the run ID from test output
3. **Check the PRs** - Look at the actual PRs created to see what went wrong
4. **Check GitHub Actions status** - Sometimes GitHub has service issues
5. **Try again** - Transient network issues can cause failures

## Next Steps

After running the tests successfully:
- Review the test output to understand the workflow
- Check workflow logs via GitHub UI or `gh run view`
- Review created PRs (before cleanup) to see AI-generated summaries
- Extend tests to cover additional scenarios
- Contribute improvements to the test suite

## References

- Test files: `tests/e2e/test_workflow_e2e.py`, `tests/e2e/test_statistics_e2e.py`
- Test runner: `tests/e2e/run_test.sh`
- Helper modules: `tests/e2e/helpers/github_helper.py`, `tests/e2e/helpers/project_manager.py`
- Fixtures: `tests/e2e/conftest.py`
- E2E workflow: `.github/workflows/e2e-test.yml`
- Recursive workflow: `.github/workflows/claudestep-test.yml`
- Migration plan: `docs/proposed/e2e-test-migration.md`
