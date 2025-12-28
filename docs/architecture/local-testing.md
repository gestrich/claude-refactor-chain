# Local Testing Setup

## Unit Testing

Unit tests are located in `tests/unit/` and provide comprehensive test coverage:

```bash
# Set Python path
export PYTHONPATH=src:scripts

# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=html

# View coverage report
coverage report --show-missing
open htmlcov/index.html  # macOS
```

Current coverage: 85%+ with 506 tests

## End-to-End Testing

End-to-end integration tests are now located in this repository at `tests/e2e/` and use a **recursive workflow pattern** where ClaudeStep tests itself.

### Purpose

The E2E tests validate the complete ClaudeStep workflow by:
- Creating test projects in the same repository (`claude-step/test-*`)
- Triggering the `claudestep-test.yml` workflow which runs the action on itself
- Verifying PRs are created correctly with AI-generated summaries
- Testing reviewer capacity limits
- Testing merge trigger functionality
- Cleaning up all test resources automatically

### Running E2E Tests Locally

```bash
# From the claude-step repository root
cd /path/to/claude-step
./tests/e2e/run_test.sh
```

**Prerequisites:**
- GitHub CLI (`gh`) installed and authenticated
- Python 3.11+ with pytest (`pip install pytest pyyaml`)
- Git configured with user.name and user.email
- Repository write access
- `ANTHROPIC_API_KEY` (optional, tests will prompt)

**Run specific tests:**
```bash
# Run only workflow tests
pytest tests/e2e/test_workflow_e2e.py -v -s

# Run only statistics tests
pytest tests/e2e/test_statistics_e2e.py -v -s

# Run a specific test function
pytest tests/e2e/test_workflow_e2e.py::test_creates_pr_with_summary -v -s
```

### How E2E Tests Work

The E2E tests use a **recursive workflow pattern**:

1. Tests create temporary test projects in `claude-step/test-project-{uuid}/`
2. Tests commit and push the test project to the main branch
3. Tests trigger the `claudestep-test.yml` workflow manually
4. The workflow runs ClaudeStep on itself using `uses: ./`
5. ClaudeStep creates PRs for the test project tasks
6. Tests verify PRs are created with summaries and cost info
7. Tests clean up all resources (projects, PRs, branches)

This pattern enables **self-contained testing** without requiring a separate demo repository.

### Test Output

Tests provide detailed progress information:

```
tests/e2e/test_workflow_e2e.py::test_creates_pr_with_summary
Creating test project: test-project-abc123
Workflow run ID: 12345678
Waiting for workflow completion...
  Status: completed (success)
Checking for PR...
  ✓ PR created with AI summary
  ✓ Cost information found
Cleaning up...
PASSED
```

### Documentation

For comprehensive E2E testing documentation, see:
- [E2E Testing Guide](e2e-testing.md) - Complete guide with troubleshooting
- [tests/e2e/README.md](../../tests/e2e/README.md) - Quick start and usage
- [Migration Plan](../proposed/e2e-test-migration.md) - Background on the recursive pattern

### GitHub Integration Testing

The tests interact with GitHub using the `gh` CLI to:
- Trigger workflows via `gh workflow run`
- Monitor workflow status via `gh run view`
- Verify PR creation and content
- Clean up test resources

All GitHub API interactions use the official `gh` CLI tool for consistency and reliability.
